#!/usr/bin/bash

# for screen command
if [ ! -d ~/.screendir ]; then
    mkdir ~/.screendir
fi
chmod 700 ~/.screendir
export SCREENDIR=$HOME/.screendir

sudo pkill -f uwsgi -9

# start elasticsearch
echo "starting Elasticsearch..."
screen -S es -X quit
sleep 2s
screen -dmS es
sleep 1s
screen -S es -X stuff $HOME'/elasticsearch-8.7.1/bin/elasticsearch'`echo -ne '\015'`
sleep 5s

# start redis
docker start redis-stack

# start fastText server
echo "starting fastText server..."
cd ./fastText/
screen -S fastText -X quit
sleep 2s
screen -dmS fastText
sleep 1s
screen -S fastText -X stuff 'uwsgi --ini app.ini'`echo -ne '\015'`
sleep 5s

# start executor
cd ../executor/
echo "initializing executor server..."
python init.py
echo "starting executor server..."
screen -S executor -X quit
sleep 2s
screen -dmS executor
sleep 1s
screen -S executor -X stuff 'uwsgi --ini app.ini'`echo -ne '\015'`
sleep 2s

# start observer
echo "starting observer..."
cd ../observer/
screen -S observer -X quit
sleep 2s
screen -dmS observer
sleep 1s
screen -S observer -X stuff 'python main.py'`echo -ne '\015'`

cd ../
echo "successfully bot started!"