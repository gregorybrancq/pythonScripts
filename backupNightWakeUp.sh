#!/bin/sh

# this script must be linked here by root user
# ln -s /home/greg/Greg/work/env/backupNight/backupNightWakeUp.sh /lib/systemd/system-sleep/backupNightWakeUp

export DISPLAY=:0.0
export XAUTHORITY=/home/greg/.Xauthority

case $1 in
    post)
        echo "Execute backupNight script from /lib/systemd/system-sleep"
        /home/greg/Greg/work/env/bin/backupNight
        ;;
esac
