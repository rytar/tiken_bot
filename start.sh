#!/bin/sh

# start elasticsearch
sudo screen -S es -X stuff 'exit'`echo -ne '\015'`
sudo screen -dmS es
sudo screen -S es -X stuff '~/elasticsearch-8.7.1/bin/elasticsearch'`echo -ne '\015'`

# start redis
docker start redis-stack

# start fastText server
cd ./fastText/
sudo screen -S fastText -X stuff 'exit'`echo -ne '\015'`
sudo screen -dmS fastText
sudo screen -S fastText -X 'uwsgi --ini app.ini'`echo -ne '\015'`

# start executor
cd ../executor/
python init.py
sudo screen -S executor -X stuff 'exit'`echo -ne '\015'`
sudo screen -dmS executor
sudo screen -S executor -X 'uwsgi --ini app.ini'`echo -ne '\015'`

# start observer
cd ../observer/
sudo screen -S observer -X stuff 'exit'`echo -ne '\015'`
sudo screen -dmS observer
sudo screen -S observer -X 'python main.py'`echo -ne '\015'`