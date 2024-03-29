# MIPS POIfier-client
Python3 deamon to get all deployments being indexed by graph-node and upload their POI (Proof-of-indexing) using referenced INDEXER_ID to the POIfier-server

**POIfier on MAINNET** - https://github.com/grassets-tech/graphrpotocol-POIfier-client

## What is MIPs
Please follow this link https://thegraph.com/blog/mips-multi-chain-indexing-incentivized-program/

![image](https://user-images.githubusercontent.com/82155440/202035124-43eb5580-92ca-4b9d-9bf3-bca3fd8dd546.png)


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
      - '--poifier-token=<RYABINA_GOERLI_POIFIER_TOKEN>'
      - '--poifier-server=<RYABINA_GOERLI_POIFIER_SERVER>'
      - '--ethereum-endpoint=<GOERLI_ENDPOINT>'
      - '--mainnet-subgraph-endpoint=https://gateway.testnet.thegraph.com/network'
      - '--graph-node-status-endpoint=<GRAPH_NODE_ENDPOINT>'
      - '--mnemonic=<OPERATOR MNEMONIC>'
      - '--indexer-address=<INDEXER_ADDRESS>'
```
NOTE:
> You can provide either `--poifier-token` you got from [goerli.poifier.io](https://goerli.poifier.io) or `--mnemonic` and `--indexer-address` and token will be generated automatically.

## Docker compose example

```
services:

  poifier-client:
    container_name: poifier-client
    image: grassets/poifier-client
    networks:
       - monitor-net
    restart: unless-stopped
    tty: true
    command:
      - '--poifier-token=0x458xxxx1c'
      - '--ethereum-endpoint=https://eth-qoerli.alchemyapi.io/v2/demo'
      - '--mainnet-subgraph-endpoint=https://gateway.testnet.thegraph.com/network'
      - '--graph-node-status-endpoint=http://index-node-0:8030/graphql'
      - '--poifier-server=https://goerli.poifier.io'
      - '--mnemonic=${MNEMONIC}'
      - '--indexer-address=${INDEXER_ADDRESS}'

```

## Docker compose with .env example 

**more .env**
```
TOKEN=0x458xxxx1c
ETH_ENDPOINT=https://eth-qoerli.alchemyapi.io/v2/demo
SUBGRAPH_ENDPOINT=https://gateway.testnet.thegraph.com/network
GRAPH_NODE=http://index-node-0:8030/graphql
POI_SERVER=https://goerli.poifier.io
MNEMONIC='test test test'
INDEXER_ADDRESS=0x123456
```

**more docker-compose.ymml**
```
services:

  poifier-client:
    container_name: poifier-client
    image: grassets/poifier-client
    networks:
       - monitor-net
    restart: unless-stopped
    tty: true
    command:
      - '--poifier-token=${TOKEN}'
      - '--ethereum-endpoint=${ETH_ENDPOINT}'
      - '--mainnet-subgraph-endpoint=${SUBGRAPH_ENDPOINT}'
      - '--graph-node-status-endpoint=${GRAPH_NODE}'
      - '--poifier-server=${POI_SERVER}'
      - '--mnemonic=${MNEMONIC}'
      - '--indexer-address=${INDEXER_ADDRESS}'

```

HINT:
> For key `--mainnet_subgraph_endpoint` you can use mainnet subgraph which is indexed locally and stored in graph-node DB.
> So, in case of docker infrastructure key would be similar to:
> * `--mainnet_subgraph_endpoint http://query-node-0:8000/subgraphs/id/Qmf5XXWA8zhHbdvWqtPcR3jFkmb5FLR4MAefEYx8E3pHfr`

## How to get "poifier-token"
Please loging with your Metamask on site https://poifier.io

# Requirements

## Python3 packages

If you run POIfier-client on `baremetal` do:

```pip3 install -r requirements.txt```

