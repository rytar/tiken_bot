#!/usr/bin/bash

# for screen command
if [ ! -d ~/.screendir ]; then
    mkdir ~/.screendir
fi
chmod 700 ~/.screendir
export SCREENDIR=$HOME/.screendir

source ./stop.sh

rm ./*/*.log

# start elasticsearch
echo "starting Elasticsearch..."
screen -dmS es
sleep 1s
screen -S es -X stuff $HOME'/elasticsearch-8.7.1/bin/elasticsearch'`echo -ne '\015'`
sleep 30s

# start redis
sudo docker start redis-stack

# start fastText server
echo "starting fastText server..."
cd ./fastText
screen -dmS fastText
sleep 1s
screen -S fastText -X stuff 'uwsgi --ini ./app.ini'`echo -ne '\015'`
sleep 30s

# start executor
echo "initializing executor server..."
cd ../executor
python3 ./init.py
echo "starting executor server..."
screen -dmS executor
sleep 1s
screen -S executor -X stuff 'uwsgi --ini ./app.ini'`echo -ne '\015'`
sleep 2s

# start observer
echo "starting observer..."
cd ../observer
screen -dmS observer
sleep 1s
screen -S observer -X stuff 'python3 ./main.py'`echo -ne '\015'`
cd ..

echo "successfully started!"