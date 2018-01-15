#!/usr/bin/env bash

PY3=/usr/bin/python3
DB=/home/mike/docker/django_mysite/db.sqlite3
SCRIPT=/home/mike/git/sonnenbattery/sonnenbattery.py
PERIOD=30

if ps ax | grep sonnenbattery.py | grep -v -q grep
then
    # the app is running, nothing to do, exit

    exit 0
else
    echo "sonnen battery crawler not running, restart the stuff"
    # python3 sonnenbattery.py 10
    $PY3 $SCRIPT $PERIOD $DB
fi

