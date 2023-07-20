#!/usr/bin/bash

echo "quit from all screens..."
screen -S es -X quit
screen -S tiken -X quit

screen -wipe

echo "successfully stopped!"