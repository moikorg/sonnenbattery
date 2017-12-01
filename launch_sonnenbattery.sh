#!/usr/bin/env bash

if ps ax | grep sonnenbattery.py | grep -v -q grep
then
    # the app is running, nothing to do, exit

    exit 0
else
    echo "sonnen battery crawler not running, restart the stuff"
    python3 sonnenbattery.py -d 10
fi

