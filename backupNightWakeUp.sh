#!/bin/sh

# To power up computer when it is in sleep mode :
#   https://forum.ubuntu-fr.org/viewtopic.php?id=1992493

# This script must be linked by root user
# ln -s /home/greg/Greg/work/env/backupNight/backupNightWakeUp.sh /lib/systemd/system-sleep/backupNightWakeUp
#
# I encountered an issue with systemd, once the program was launched, it was killed by systemd-sleep after 90s
#   systemd-sleep: (sd-executor) terminated by signal ALRM
# linked to systemd-cron program (https://bugs.python.org/issue26839)

export DISPLAY=:0.0
export XAUTHORITY=/home/greg/.Xauthority

case $1 in
    post)
        echo "Execute backupNight script from /lib/systemd/system-sleep"
        /home/greg/Greg/work/env/bin/backupNight
        ;;
esac
