########################################################################
# POIfier-client - script to upload POI to POIFier POIfier-server
# author: Grassets-tech
# contact: contact@grassets.tech
########################################################################
#!/usr/bin/env python3

import argparse
import requests
from python_graphql_client import GraphqlClient
from string import Template
import base58
import sys
import os
import glob
import json
import time
import logging
import syslog

# pip3 install base58
# pip3 install python-graphql-client
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
INDEXER_REF = '0x0000000000000000000000000000000000000000'

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--indexer_graph_node_endpoint',
        help='graph-node endpoint, e.g.: http://index-node-0:8030/graphql',
        default='http://index-node-0:8030/graphql',
        type=str)
    parser.add_argument('--poifier_token',
        help='token, request token via portal',
        required=True,
        type=str)
    parser.add_argument('--poifier_server',
        help='token, request token via portal',
        default='https://poi-hub-9mwaq.ondigitalocean.app/api/poi',
        type=str)
    parser.add_argument('--mainnet_subgraph_endpoint',
        help='graph network endpoint (default: %(default)s)',
        default='https://gateway.network.thegraph.com/network',
        type=str)
    parser.add_argument('--ethereum_endpoint',
        help='ethereum endpoint to request block hash (default: %(default)s)',
        default='https://eth-mainnet.alchemyapi.io/v2/demo',
        type=str)
    return parser.parse_args()

def getSubgraphs(indexer_id, graphql_endpoint):
    client = GraphqlClient(endpoint=graphql_endpoint)
    subgraphs = []
    query = "{indexingStatuses {node synced subgraph health}}"
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
        subgraphs = data['data']['indexingStatuses']
    return subgraphs

def getCurrentEpoch(subgraph_endpoint):
    client = GraphqlClient(endpoint=subgraph_endpoint)
    query = """{ graphNetworks { currentEpoch } }"""
    logging.info('Quering currentEpoch endpoint: {} query: {}'.format(subgraph_endpoint, query))
    try:
        data = client.execute(query=query)
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get current Epoch, check endpoint {}'.format(e))
        sys.exit()
    if data.get("errors"):
        logging.error('Can\'t get current Epoch, check query {}'.format(data))
        sys.exit()
    logging.info('Received currentEpoch data: {}'.format(data))
    return data['data']['graphNetworks'][0]['currentEpoch']

def getStartBlock(epoch, subgraph_endpoint):
    t = Template("""query StartBlock { epoch(id: $epoch) { startBlock } }""")
    client = GraphqlClient(endpoint=subgraph_endpoint)
    query = t.substitute(epoch=epoch)
    logging.info('Quering startBlock endpoint: {} query: {}'.format(subgraph_endpoint, query))
    try:
        data = client.execute(query=query)
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get startBlock, check endpoint {}'.format(e))
        sys.exit()
    if data.get("errors"):
        logging.error('Can\'t get startBlock, check query {}'.format(data))
        sys.exit()
    logging.info('Received startBlock data: {}'.format(data))
    return data['data']['epoch']['startBlock']

def getBlockHash(block_number, ethereum_endpoint):
    payload = {
        'method': 'eth_getBlockByNumber',
        'params': ['{}'.format(hex(block_number)), False],
        'jsonrpc': '2.0',
        'id': 1,
    }
    logging.info('Quering Block hash: {} query: {}'.format(ethereum_endpoint, payload))
    try:
        response = requests.post(ethereum_endpoint, json=payload).json()
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get Block hash, check connection {}'.format(e))
        sys.exit()
    if response.get("error"):
        logging.error('Can\'t get Block hash, check endpoint {}'.format(response))
        sys.exit()
    if not response.get("result"):
        logging.error('Can\'t get Block hash, check block number {}'.format(response))
        sys.exit()
    logging.info('Received Block hash: {}'.format(response["result"]["hash"]))
    return response["result"]["hash"]

def getCurrentBlock(ethereum_endpoint):
    payload = {
        'method': 'eth_blockNumber',
        'params': [],
        'jsonrpc': '2.0',
        'id': 1,
    }
    try:
        response = requests.post(ethereum_endpoint, json=payload).json()
    except requests.exceptions.RequestException as e:
        logging.error('Can\'t get Block, check connection {}'.format(e))
        sys.exit()
    if response.get("error"):
        logging.error('Can\'t get Block, check endpoint {}'.format(response))
        sys.exit()
    if not response.get("result"):
        logging.error('Can\'t get Block {}'.format(response))
        sys.exit()
    logging.info('Received Block: {}'.format(response.get("result")))
    return int(response['result'], 16)

def getPoi(indexer_id, block_number, block_hash, subgraph_ipfs_hash, graphql_endpoint):
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
    syslog.syslog(syslog.LOG_INFO, 'Quering POI endpoint: {} query: {}'.format(graphql_endpoint, query))
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
        syslog.info('Warning: no POI found for subgraph {}'.format(subgraph_ipfs_hash))
    return poi

def uploadPoi(args, report):
    token = '{}:{}'.format(args.indexer_id, args.token)
    headers = {
    "Content-Type": "application/json",
    "token": token
    }
    try:
        r = requests.post(args.poifier_server, headers=headers, json=report)
    except Exception as e:
        logging.error('Failed to upload POI report {}'.format(e))
    if r.status_code != 200:
        logging.error('Failed to upload POI report {}'.format(r.status_code))

def getEpochBlockRange(epoch_range, args):
    epoch_block_range = []
    for epoch in epoch_range:
        block_number = getStartBlock(epoch, args.mainnet_subgraph_endpoint)
        block_hash = getBlockHash(block_number, args.ethereum_endpoint)
        epoch_block_range.append({'epoch': epoch, 'block': block_number, 'hash': block_hash})
    return  epoch_block_range

def getBlockHashRange(block_range, args):
    block_hash_range = []
    for block_number in block_range:
        block_hash = getBlockHash(block_number, args.ethereum_endpoint)
        block_hash_range.append({'block': block_number, 'hash': block_hash})
    return block_hash_range

def getPoiReport(subgraphs, epoch_block_range, block_hash_range, args):
    poi_report = []
    for subgraph in subgraphs:
        for epoch in epoch_block_range:
            poi = getPoi(INDEXER_REF, epoch['block'], epoch['hash'], subgraph['subgraph'], args.indexer_graph_node_endpoint)
            if poi:
                poi_report.append({'epoch':epoch['epoch'], 'deployment': subgraph['subgraph'], 'poi': poi})
        for block in block_hash_range:
            poi = getPoi(INDEXER_REF, block['block'], block['hash'], subgraph['subgraph'], args.indexer_graph_node_endpoint)
            if poi:
                poi_report.append({'block':block['block'], 'deployment': subgraph['subgraph'], 'poi': poi})
    return poi_report

def main():
    while True:
        time.sleep(15)
        args = parseArguments()
        current_epoch = getCurrentEpoch(args.mainnet_subgraph_endpoint)
        current_block = getCurrentBlock(args.ethereum_endpoint)
        subgraphs = getSubgraphs(args.indexer_id, args.indexer_graph_node_endpoint)
        epoch_range = range(current_epoch-9, current_epoch+1)
        block_range = [(current_block // 1000 - i) * 1000 for i in range(0,10)]
        epoch_block_range = getEpochBlockRange(epoch_range, args)
        block_hash_range = getBlockHashRange(block_range, args)
        poi_report = getPoiReport(subgraphs, epoch_block_range, block_hash_range, args)
        for item in poi_report:
            logging.info(item)
        uploadPoi(args, poi_report)
        time.sleep(14400) # Run script every 4 hrs

if __name__ == "__main__":
    main()
