#!/usr/bin/bash
# install libraries
pip install -r ./requirements.txt

# install redis
docker create --name redis-stack -p 6379:6379 redis/redis-stack:latest

# install Elasticsearch
if [ ! -d ~/elasticsearch-8.7.1 ]; then
    cd ~
    wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.7.1-linux-x86_64.tar.gz
    wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.7.1-linux-x86_64.tar.gz.sha512
    shasum -a 512 -c elasticsearch-8.7.1-linux-x86_64.tar.gz.sha512
    tar -xzf elasticsearch-8.7.1-linux-x86_64.tar.gz
    cd ~/elasticsearch-8.7.1
    ./bin/elasticsearch
fi