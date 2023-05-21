#!/bin/sh

# start elasticsearch
screen -dmS es
screen -S es -X stuff '~/elasticsearch-8.7.1/bin/elasticsearch'`echo -ne '\015'`

# start redis
sudo service docker start
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
cd ./executor/
python init.py

# start fastText server
cd ../fastText/
screen -dmS fastText
screen -S fastText -X 'uwsgi --ini app.ini'`echo -ne '\015'`

# start executor
cd ../executor/
screen -dmS executor
screen -S executor -X 'uwsgi --ini app.ini'`echo -ne '\015'`

# start observer
cd ../observer/
screen -dmS observer
screen -S observer -X 'python main.py'`echo -ne '\015'`