#!/usr/bin/env bash

PY3=/usr/bin/python3
SCRIPT=/home/mike/git/sonnenbattery/sonnenbattery.py
CONFIG=/home/mike/git/sonnenbattery/config.rc
PERIOD=10

if ps ax | grep sonnenbattery.py | grep -v -q grep
then
    # the app is running, nothing to do, exit
    #echo "App already running"
    exit 0
else
    echo "sonnen battery crawler not running, restart the stuff"
    # python3 sonnenbattery.py 10
    $PY3 $SCRIPT -d -p $PERIOD -f $CONFIG 2>&1 
fi

