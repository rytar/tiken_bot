#!/usr/bin/bash

echo "killing all uwsgi process..."
sudo pkill -f uwsgi -9

echo "quit from all screens..."
screen -S es -X quit
screen -S fastText -X quit
screen -S executor -X quit
screen -S observer -X quit

screen -wipe

echo "successfully stopped!"