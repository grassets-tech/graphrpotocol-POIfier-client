########################################################################
# POIfier-client - script to upload POI to POIfier-server
# author: Grassets-tech
# contact: contact@grassets.tech
########################################################################
#!/usr/bin/env python3

import argparse
import logging
import requests
import sys
import time
from python_graphql_client import GraphqlClient
from string import Template
from urllib.parse import urljoin
from hdwallet import HDWallet
from hdwallet.symbols import ETH
from eth_account.messages import encode_defunct
from web3 import Web3

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
INDEXER_REF = '0x0000000000000000000000000000000000000000'
LAST_N_EPOCH = 10
LAST_N_1K_BLOCK = 10
SLEEP = 14400 # Run script every 4 hrs
MSG = 'RYABINA_POI_HUB'

CHAIN_BY_CAIP2_AlIAS = {
  'eip155:1': 'mainnet',
  'eip155:5': 'goerli',
  'eip155:100': 'gnosis',
  'eip155:42161': 'arbitrum-one',
  'eip155:421613': 'arbitrum-goerli',
  'eip155:43114': 'avalanche',
  'eip155:137': 'polygon',
  'eip155:42220': 'celo',
  'eip155:10': 'optimism',
}

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graph-node-status-endpoint',
        dest='graph_node_status_endpoint',
        help='Graph-node status endpoint, (default: %(default)s)',
        default='http://index-node-0:8030/graphql',
        type=str)
    parser.add_argument('--poifier-token',
        dest='poifier_token',
        help='Auth token, request token via POIfier portal or provide keys --mnemonic and --indexer-address',
        type=str)
    parser.add_argument('--poifier-server',
        dest='poifier_server',
        help='URL of POIfier server (default: %(default)s)',
        default='https://poifier.io',
        required=True,
        type=str)
    parser.add_argument('--indexer-agent-epoch-subgraph-endpoint',
        dest='indexer_agent_epoch_subgraph_endpoint',
        help='Epoch subgraph for Epoch Oracle (default: %(default)s)',
        default='',
        required=True,
        type=str)
    parser.add_argument('--mnemonic',
        dest='mnemonic',
        help='Provide an Operator mnemonic if --poifier-token is not provided',
        type=str)
    parser.add_argument('--indexer-address',
        dest='indexer_address',
        help='Provide Indexer address if --poifier-token is not provided',
        type=str) 
    return parser.parse_args()

def validate_token_keys(args):
    if not args.poifier_token and not all([args.mnemonic, args.indexer_address]):
        logging.error('Either --poifier-token or pair --mnemonic and --indexer-address MUST be provided')
        sys.exit()

def get_token(mnemonic, indexer_address):
    """ Gets token for uploading poi to poifier server. """
    hdwallet = HDWallet(symbol=ETH)
    hdwallet.from_mnemonic(mnemonic=mnemonic)
    hdwallet.from_path(path="m/44'/60'/0'/0/0")
    private_key = hdwallet.private_key()

    web3 = Web3()
    msghash = encode_defunct(text=MSG)
    sign_hash = web3.eth.account.sign_message(msghash, private_key)
    logging.info('Message signed with: {}'.format(sign_hash.signature.hex()))
    poifier_token = '{}:{}'.format(indexer_address.lower(),sign_hash.signature.hex())
    logging.info('POIfier TOKEN: {}'.format(poifier_token))
    return poifier_token

def get_subgraphs(graphql_endpoint):
    """ Gets subgraphs from the given node.

    Queries local graph node to get subgraphs grouped by network.

    Returns: Dictionary of subgraphs
    """
    subgraphs = {}
    client = GraphqlClient(endpoint=graphql_endpoint)
    query = """
                query {
                    indexingStatuses {
                        subgraph
                        health
                        chains {
                        network
                        chainHeadBlock {
                            number
                        }
                        }
                    }
                }
                """
    logging.info('Quering subgraphs endpoint: {} query: {}'.format(graphql_endpoint, query))
    try:
        data = client.execute(query=query)
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get subgraphs, check endpoint {}'.format(e))
        sys.exit()
    if data.get('errors'):
        logging.error('Can\'t get subgraphs, check query {}'.format(data))
        sys.exit()
    logging.info('Received subgraphs data: {}'.format(data))
    if data:
        for subgraph in data['data']['indexingStatuses']:
            if subgraph['health'] == 'healthy':
                subgraphs[subgraph['subgraph']] = {
                    'network': subgraph['chains'][0]['network'],
                    'chainHeadBlock': int(subgraph['chains'][0]['chainHeadBlock']['number']),
                }
        for key, val in subgraphs.items():
            logging.info('{}:{}'.format(key,val))
    return subgraphs

def get_last_n_epochs_from_oracle(graphql_endpoint):
    client = GraphqlClient(endpoint=graphql_endpoint)
    t = Template("""
                    query network{
                        networks {
                            id
                            blockNumbers (first: $n, orderBy: epochNumber, orderDirection: desc){
                                epochNumber
                                blockNumber
                                }
                            }
                        }
                """)
    query = t.substitute(n=LAST_N_EPOCH)
    logging.info('Quering Epochs from Oracle: {} query: {}'.format(graphql_endpoint, query))
    try:
        data = client.execute(query=query)
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get Epochs, check endpoint {}'.format(e))
        sys.exit()
    logging.info('Received Epochs data: {}'.format(data))
    if data.get('errors'):
        logging.error('Can\'t get Epochs, check query {}'.format(data))
        sys.exit()
    if len(data.get('data')) == 0:
        logging.error('Can\'t get Epochs, check endpoint {}'.format(e))
        sys.exit()
    networks = data['data']['networks']
    epochs = {}
    for network in networks:
        epochs[CHAIN_BY_CAIP2_AlIAS.get(network['id'])] = network['blockNumbers']
    for key, val in epochs.items():
        logging.info('{}:{}'.format(key,val))   
    return epochs

def get_hash_from_block(graphql_endpoint, network, block_number):
    client = GraphqlClient(endpoint=graphql_endpoint)
    t = Template(""" query BlockHash { blockHashFromNumber(network: "$network", blockNumber: $block_number)} """)
    query = t.substitute(network=network, block_number=block_number)
    logging.info('Quering BlockHash: {} query: {}'.format(graphql_endpoint, query))
    try:
        data = client.execute(query=query)
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get BlockHash, check endpoint {}'.format(e))
        sys.exit()
    logging.info('Received BlockHash data: {}'.format(data))
    if data.get('errors'):
        logging.error('Can\'t get BlockHash, check query {}'.format(data))
        sys.exit()
    if len(data.get('data')) == 0:
        logging.error('Can\'t get BlockHash, check endpoint {}'.format(e))
        sys.exit()
    block_hash = data['data']['blockHashFromNumber']
    return block_hash

def get_poi(indexer_id, block_number, block_hash, subgraph_ipfs_hash, graphql_endpoint):
    """ Gets POI from graph node for given subgraph for given block. """
    poi = ''
    client = GraphqlClient(endpoint=graphql_endpoint)
    t = Template("""query RefPOI {
                        proofOfIndexing(
                        subgraph: "$subgraph_ipfs_hash",
                        blockNumber: $block_number,
                        blockHash: "$block_hash",
                        indexer: "$indexer_id")
                    }""")
    query = t.substitute(subgraph_ipfs_hash=subgraph_ipfs_hash,
                              block_number=block_number,
                              block_hash=block_hash,
                              indexer_id=indexer_id)
    logging.info('Quering POI endpoint: {} query: {}'.format(graphql_endpoint, query))
    try:
        data = client.execute(query=query)
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get POI, check endpoint {}'.format(e))
        sys.exit()
    logging.info('Received POI data: {}'.format(data))
    if data.get('errors'):
        logging.error('Can\'t get POI, check query {}'.format(data))
        sys.exit()
    if len(data.get('data')) == 0:
        logging.error('Can\'t get POI, check endpoint {}'.format(e))
        sys.exit()
    poi = data['data']['proofOfIndexing']
    if not poi:
        logging.info('Warning: no POI found for subgraph {}'.format(subgraph_ipfs_hash))
    return poi

def get_last_n_block_range(subgraphs):
    block_range = {}
    for subgraph, attr in subgraphs.items():
        if not block_range.get(attr['network']):
            block_range[attr['network']] = [(attr['chainHeadBlock'] // 1000 - i) * 1000 for i in range(0,LAST_N_1K_BLOCK)]
    return block_range

def get_last_n_block_hash_range(block_range, graphql_endpoint):
    block_hash_range = {}
    for network, blocks in block_range.items():
        for block_number in blocks:
            block_hash = get_hash_from_block(graphql_endpoint, network, block_number)
            if not block_hash_range.get(network):
                block_hash_range[network] = [{'block': block_number, 'hash': block_hash}]
            else:
                block_hash_range[network].append({'block': block_number, 'hash': block_hash})
    return block_hash_range

def get_poi_report_by_n_blocks(subgraphs, block_hash_range, graphql_endpoint):
    poi_report = []
    for subgraph, attr in subgraphs.items():
        for block_hash in block_hash_range[attr['network']]:
            poi = get_poi(INDEXER_REF, block_hash['block'], block_hash['hash'], subgraph, graphql_endpoint)
            if poi:
                poi_report.append({'block':block_hash['block'], 'deployment': subgraph, 'poi': poi})
    return poi_report

def get_poi_report_by_n_epochs(subgraphs, epochs, graphql_endpoint):
    poi_report = []
    for subgraph, attr in subgraphs.items():
        for epoch_block in epochs[attr['network']]:
            block_hash=get_hash_from_block(graphql_endpoint, attr['network'], int(epoch_block['blockNumber']))
            poi = get_poi(INDEXER_REF, int(epoch_block['blockNumber']), block_hash, subgraph, graphql_endpoint)
            if poi:
                poi_report.append({'epoch': int(epoch_block['epochNumber']), 'block':int(epoch_block['blockNumber']), 'deployment': subgraph, 'poi': poi})
    return poi_report

def getSummary(poi_report):
    deployments_count = len(set([i['deployment'] for i in poi_report]))
    records_count = len(poi_report)
    return deployments_count, records_count

def upload_poi(poifier_server_url, token, report):
    """ Uploads POI report to the poifier server. """
    headers = {
    "Content-Type": "application/json",
    "token": token
    }
    poifier_server_url_api = urljoin(poifier_server_url, '/api/poi')
    try:
        r = requests.post(poifier_server_url_api, headers=headers, json=report)
    except Exception as e:
        logging.error('Failed to upload POI report {}'.format(e))
        return
    if r.status_code != 200:
        logging.error('Failed to upload POI report to poifier-server: {}, Error: {}, {}'.format(poifier_server_url_api, r.status_code, r.text))
        return
    logging.info('POI report uploaded to poifier-server: {}'.format(poifier_server_url_api))


def main():
    while True:
        start_time = time.time()
        logging.info('POIfier started...')
        args = parseArguments()
        validate_token_keys(args)
        poifier_token = args.poifier_token if args.poifier_token else get_token(args.mnemonic, args.indexer_address)
        subgraphs = get_subgraphs(args.graph_node_status_endpoint)
        block_range = get_last_n_block_range(subgraphs)
        block_hash_range = get_last_n_block_hash_range(block_range, args.graph_node_status_endpoint)
        epoch_range = get_last_n_epochs_from_oracle(args.indexer_agent_epoch_subgraph_endpoint)
        poi_by_block = get_poi_report_by_n_blocks(subgraphs, block_hash_range, args.graph_node_status_endpoint)
        poi_by_epoch = get_poi_report_by_n_epochs(subgraphs, epoch_range, args.graph_node_status_endpoint)
        poi_report = [*poi_by_block, *poi_by_epoch]
        for item in poi_report:
            logging.info(item)
        logging.info('----------------------------------------')
        logging.info('POI summary: deployments: {}, records: {}'.format(*getSummary(poi_report)))
        logging.info('POI token: {}'.format(poifier_token))
        if len(poi_report) > 0:
            upload_poi(args.poifier_server, poifier_token, poi_report)
        logging.info('POIfier finished in {}'.format(time.time() - start_time))
        logging.info('----------------------------------------')
        logging.info('POIfier sleeping ...')
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()
