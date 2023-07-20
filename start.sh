#!/usr/bin/bash

# for screen command
if [ ! -d ~/.screendir ]; then
    mkdir ~/.screendir
fi
chmod 700 ~/.screendir
export SCREENDIR=$HOME/.screendir

source ./stop.sh

rm ./*.log

# start elasticsearch
echo "starting Elasticsearch..."
screen -dmS es
sleep 1s
screen -S es -X stuff $HOME'/elasticsearch-8.7.1/bin/elasticsearch'`echo -ne '\015'`
sleep 30s

# start redis
sudo docker start redis-stack

# start
screen -dmS tiken
sleep 1s
screen -S tiken -X stuff 'python3 ./src/main.py'`echo -ne '\015'`

echo "successfully started!"