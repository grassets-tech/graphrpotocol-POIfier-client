# POIfier-client

Python3 script to get all deployments from graph-node and upload POI using referenced INDEXER_ID to the POIfier-server

## Docker
docker pull ghcr.io/grassets-tech/poifier-client

## Docker compose
see docker-compose.yml file as an example provided

## Usage example:

```bash
$ python3 poifier-client.py --help
usage: poifier-client.py [-h] --indexer_graph_node_endpoint INDEXER_GRAPH_NODE_ENDPOINT --indexer_id INDEXER_ID --poifier_token POIFIER_TOKEN [--mainnet_subgraph_endpoint MAINNET_SUBGRAPH_ENDPOINT]
                         [--ethereum_endpoint ETHEREUM_ENDPOINT]

optional arguments:
  -h, --help            show this help message and exit
  --indexer_graph_node_endpoint INDEXER_GRAPH_NODE_ENDPOINT
                        graph-node endpoint, e.g.: http://index-node-0:8030/graphql
  --indexer_id INDEXER_ID
                        indexer_id, shoudl be small chars e.g.: 0x1234abc...
  --poifier_token POIFIER_TOKEN
                        token, request token via portal
  --mainnet_subgraph_endpoint MAINNET_SUBGRAPH_ENDPOINT
                        graph network endpoint (default: https://gateway.network.thegraph.com/network)
  --ethereum_endpoint ETHEREUM_ENDPOINT
                        ethereum endpoint to request block hash (default: https://eth-mainnet.alchemyapi.io/v2/demo)
```

# Requirements

## Python3 packages

```pip3 install -r requirements.txt```
