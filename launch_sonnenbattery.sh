#!/usr/bin/env bash

PY3=/usr/bin/python3
SCRIPT=/home/mike/git/sonnenbattery/sonnenbattery.py

if ps ax | grep sonnenbattery.py | grep -v -q grep
then
    # the app is running, nothing to do, exit

    exit 0
else
    echo "sonnen battery crawler not running, restart the stuff"
    # python3 sonnenbattery.py 10
    $PY3 $SCRIPT 10
fi

