# POIfier-client

Python3 deamon to get all deployments being indexed by graph-node and upload their POI (Proof-of-indexing) using referenced INDEXER_ID to the POIfier-server

# Goal

The main goal of this project is to help Graphprotocol Indexer to verify consistency of their indexed data by uploading POI (Proof-of-indexing) data to POIfier-server periodically.

# Design

* **POIfier-client:** to be run by Indexer (locally or remotelly).
  * Client queries graph-node to get list of subgraph deployments which are being indexed or were indexed by node
  * Requests graph-node to generate `referenced` POI for `referenced` indexer id=`0x000..0` for last N=10 Epochs and N=10 Eth Blocks (block of 1000)
  * Uploads report to POIfier-server

* **POIfier-server:** (developed by [Ryabina](https://github.com/Ryabina-io)) collects and organizes POI data provided by POIfier-client 


# How to use

## Docker

Pull docker image

`docker pull grassets/poifier-client`


## Docker compose

```
version: '2.1'

networks:
  monitor-net:
    driver: bridge
services:
  poifier-client:
    container_name: poifier-client
    image: grassets/poifier-client
    networks:
       - monitor-net
    restart: unless-stopped
    tty: true
    command:
      - '--poifier_token=<POIFIER_TOKEN>'
      - '--poifier_server=POIFIER_SERVER'
      - '--ethereum_endpoint=<ETHEREUM_ENDPOINT>'
      - '--mainnet_subgraph_endpoint=<MAINNET_GRAPH_SUBGRAPH>'
      - '--indexer_graph_node_endpoint=<GRAPH_NODE_ENDPOINT>'

```

## How to run

```bash
$ python3 poifier-client.py --help
usage: poifier-client.py [-h] [--indexer_graph_node_endpoint INDEXER_GRAPH_NODE_ENDPOINT] --poifier_token POIFIER_TOKEN [--poifier_server POIFIER_SERVER]
                         [--mainnet_subgraph_endpoint MAINNET_SUBGRAPH_ENDPOINT] [--ethereum_endpoint ETHEREUM_ENDPOINT]

optional arguments:
  -h, --help            show this help message and exit
  --indexer_graph_node_endpoint INDEXER_GRAPH_NODE_ENDPOINT
                        Graph-node endpoint, (default: http://index-node-0:8030/graphql)
  --poifier_token POIFIER_TOKEN
                        Auth token, request token via POIfier portal
  --poifier_server POIFIER_SERVER
                        URL of POIfier server (default: https://api.poifier.io)
  --mainnet_subgraph_endpoint MAINNET_SUBGRAPH_ENDPOINT
                        Graph network endpoint (default: https://gateway.network.thegraph.com/network)
  --ethereum_endpoint ETHEREUM_ENDPOINT
                        ethereum endpoint to request block hash (default: https://eth-mainnet.alchemyapi.io/v2/demo)
```

HINT:
> For key `--mainnet_subgraph_endpoint` you can use mainnet subgraph which is indexed locally and stored in graph-node DB.
> So, in case of docker infrastructure key would be similar to:
> * `--mainnet_subgraph_endpoint http://query-node-0:8000/subgraphs/id/Qmf5XXWA8zhHbdvWqtPcR3jFkmb5FLR4MAefEYx8E3pHfr`


# Requirements

## Python3 packages

If you run POIfier-client on `baremetal` do:

```pip3 install -r requirements.txt```
