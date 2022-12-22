# POIfier-client
![made-with-python](https://img.shields.io/badge/made%20with-Python3-1f425f.svg)
![Docker Cloud Automated build](https://img.shields.io/docker/cloud/automated/grassets/poifier-client?color=green)
![image version](https://img.shields.io/docker/v/grassets/poifier-client?sort=semver)
![Docker Image Pulls](https://img.shields.io/docker/pulls/grassets/poifier-client.svg)

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

 - **The Graph MIPs Indexers**: please follow [POIfier for MIPS](https://github.com/grassets-tech/graphrpotocol-POIfier-client/blob/main/MIPs/poifier-client-mips.md)


## Docker

Pull docker image

`docker pull grassets/poifier-client`


## Docker compose

```
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
      - '--graph-node-status-endpoint=${GRAPH_NODE}'
      - '--poifier-server=${POI_SERVER}'
      - '--mnemonic=${MNEMONIC}'
      - '--indexer-address=${INDEXER_ADDRESS}'
      - '--indexer-agent-epoch-subgraph-endpoint=${INDEXER_AGENT_EPOCH_SUBGRAPH_ENDPOINT}'

```
NOTE:
> You can provide either `--poifier-token` you got from [poifier.io](https://poifier.io) or `--mnemonic` and `--indexer-address` and token will be generated automatically.

## How to run

```bash
$ python3 poifier-client.py --help
usage: poifier.py [-h] [--graph-node-status-endpoint GRAPH_NODE_STATUS_ENDPOINT] [--poifier-token POIFIER_TOKEN] --poifier-server POIFIER_SERVER --indexer-agent-epoch-subgraph-endpoint
                  INDEXER_AGENT_EPOCH_SUBGRAPH_ENDPOINT [--mnemonic MNEMONIC] [--indexer-address INDEXER_ADDRESS]

options:
  -h, --help            show this help message and exit
  --graph-node-status-endpoint GRAPH_NODE_STATUS_ENDPOINT
                        Graph-node status endpoint, (default: http://index-node-0:8030/graphql)
  --poifier-token POIFIER_TOKEN
                        Auth token, request token via POIfier portal or provide keys --mnemonic and --indexer-address
  --poifier-server POIFIER_SERVER
                        URL of POIfier server (default: https://poifier.io)
  --indexer-agent-epoch-subgraph-endpoint INDEXER_AGENT_EPOCH_SUBGRAPH_ENDPOINT
                        Epoch subgraph for Epoch Oracle (default: )
  --mnemonic MNEMONIC   Provide an Operator mnemonic if --poifier-token is not provided
  --indexer-address INDEXER_ADDRESS
                        Provide Indexer address if --poifier-token is not provided
```

# Requirements

## Python3 packages

If you run POIfier-client on `baremetal` do:

```pip3 install -r requirements.txt```

>> WARNING:
# How to update container

```
sudo docker-compose stop poifier-client
sudo docker rm poifier-client
sudo docker image rm grassets/poifier-client
sudo docker-compose up -d 
sudo docker logs -f poifier-client

```
