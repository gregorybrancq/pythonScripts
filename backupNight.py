#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
To use computer when it is not used, make the backup during the night.
It will compute the different backups configuration, turn off/on screens to reduce power consumption.

To power up computer when it is in sleep mode :
https://forum.ubuntu-fr.org/viewtopic.php?id=1992493

To launch this program after resuming :
Create a file in  /lib/systemd/system-sleep/backupNight
#!/bin/sh
case $1/$2 in
  post/*)
    echo "Execute backupNight script in /lib/systemd/system-sleep..."
    /home/greg/Greg/work/env/bin/backupNight
    # Place your post suspend (resume) commands here, or `exit 0` if no post suspend action required
    ;;
esac
"""

import os
import subprocess
import sys
from datetime import datetime
from optparse import OptionParser

sys.path.append('/home/greg/Greg/work/env/projects/pythonCommon')
from progDisEn import ProgEnDis
from mail import sendMail


##############################################
#              Line Parsing                 ##
##############################################

parser = OptionParser()

parser.add_option(
    "--debug",
    action="store_true",
    dest="debug",
    default=False,
    help="Display all debug information.--backup_now"
)

parser.add_option(
    "--backup_now",
    action="store_true",
    dest="backup_now",
    default=False,
    help="Computes backup immediately."
)

parser.add_option(
    "--dry_run",
    action="store_true",
    dest="dry_run",
    default=False,
    help="Just print what it will do."
)

parser.add_option(
    "-e",
    "--enable",
    action="store_true",
    dest="enable",
    default=False,
    help="Enable this program."
)

parser.add_option(
    "-d",
    "--disable",
    action="store_true",
    dest="disable",
    default=False,
    help="Disable this program for one night."
)

(parsedArgs, args) = parser.parse_args()

##############################################


##############################################
# Global variables
##############################################

progName = "backupNight"

# TODO logging
## load config
#logging.config.fileConfig(os.path.join(scriptDir, 'logging.conf'))
## disable logging
#logging.disable(sys.maxsize)
## create logger
#log = logging.getLogger(progName)
#
#logFile = os.path.join(logDir, progName + "_"
#                       + str(datetime.today().isoformat("_") + ".log"))
configFile  = os.path.join("/home/greg/Greg/work/config", progName, progName + ".cfg")
runningFile = os.path.join("/tmp", progName + ".running")
disableFile = os.path.join("/tmp", progName + ".disable")

userMail = "gregory.brancq@free.fr"

##############################################


##############################################
# Class
##############################################

class Backups:
    def __init__(self):
        self.cfgs = dict()
        self.add()

    def __str__(self):
        res = str()
        for cfg in self.cfgs.keys():
            res += "Config " + cfg + "\n"
            res += str(self.cfgs[cfg])
        return res

    def add(self):
        self.cfgs["home"] = Backup(name="Home", periods=["yearly", "monthly", "weekly", "daily"],
                                   cfgFile="/home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf")
        self.cfgs["vps"] = Backup(name="Vps", periods=["yearly", "monthly", "weekly", "daily"],
                                  cfgFile="/home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf")

    def run(self):
        for cfg in self.cfgs.keys():
            self.cfgs[cfg].run()


class Backup:
    def __init__(self, name, periods, cfgFile):
        self.name = name
        self.periods = periods
        self.cfg = cfgFile
        self.cmd = str()

    def __str__(self):
        res = str()
        res += "  config file = " + self.cfg + "\n"
        res += "  periods     = " + str(self.periods) + "\n"
        return res

    def run(self):
        for period in self.periods:
            periodC = Period(period)
            if periodC.canBeLaunch() :
                cmd = ["/usr/bin/rsnapshot", "-c", self.cfg, period]
                if parsedArgs.dry_run:
                    print("Command to launch :\n" + str(cmd))
                else:
                    procBackup = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    res = procBackup.communicate()
                    msg = res[0]
                    err = res[1]
                    if procBackup.returncode == 0 :
                        if period == "daily" :
                            procParsed = subprocess.Popen(["/usr/local/bin/rsnapreport.pl"],
                                        stdin = subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            outReport = procParsed.communicate(input=msg)[0]
                            sendMail(From=userMail, To=userMail,
                                     Subject="Rsnapshot " + self.name + " : " + period,
                                     Message=outReport + "\n\nMessage log :\n" + msg + "\n\nError log : \n" + err)
                        else :
                            sendMail(From=userMail, To=userMail,
                                     Subject="Rsnapshot " + self.name + " : " + period,
                                     Message="Message log :\n" + msg + "\n\nError log : \n" + err)
                    else :
                        sendMail(From=userMail, To=userMail,
                                 Subject="Error with rsnapshot " + self.name + " : " + period,
                                 Message="Error log : \n" + err + "\n\nMessage log :\n" + msg)


class Period:

    def __init__(self, periodName):
        self.curDay = datetime.now().weekday()
        self.curDate =datetime.now().day
        self.curMonth = datetime.now().month
        self.period = periodName
        self.level = str()
        self.cmd = str()

    def canBeLaunch(self):
        if self.period == "daily":
            return True
        elif self.period == "weekly":
            if self.curDay == 0 : # monday
                return True
        elif self.period == "monthly":
            if self.curDay == 0 : # monday
                if self.curDate < 8 : # first week of the month
                    return True
        elif self.period == "yearly":
            if self.curDay == 0 : # monday
                if self.curDate < 8 : # first week of the month
                    if self.curMonth == 1 or self.curMonth == 7 : # month : january(=1) or july(=7)
                        return True
        return False

##############################################


##############################################
# Functions
##############################################

def inGoodTime():
    curHour = datetime.now().hour
    if curHour >= 16 :
        return True
    return False

def alreadyLaunchedToday():
    if not os.path.isfile(configFile) :
        return False
    else :
        fd = open(configFile, 'r')
        dateFileStr = fd.read().rstrip('\n')
        try :
            configDate = datetime.strptime(dateFileStr, "%Y-%m-%d")
        except ValueError :
            return True
        currentDT = datetime.now().date()
        if configDate == currentDT:
            return True
        return False

def createCfgFile():
    if os.path.isfile(configFile) :
        os.remove(configFile)
    try :
        fd = open(configFile, 'w')
        fd.write(str(datetime.now().date()))
        fd.close()
    except :
        print("Error during configFile creation " + configFile)

def computeBackups():
    backups = Backups()
    if parsedArgs.dry_run:
        print(str(backups))
    backups.run()

def computeWake():
    # to wakeup computer
    #echo 0 > /sys/class/rtc/rtc0/wakealarm && date '+%s' -d '+ 1 minutes' > /sys/class/rtc/rtc0/wakealarm
    # to check
    #grep 'al\|time' < /proc/driver/rtc
    cmd = 'echo 0 > /sys/class/rtc/rtc0/wakealarm && date -u --date "Tomorrow 03:00:00" +%s  > ' \
          '/sys/class/rtc/rtc0/wakealarm '
    os.system(cmd)

def screenOn():
    subprocess.call(["xset", "dpms", "force", "on"])

def screenOff():
    subprocess.call(["xset", "dpms", "force", "off"])

##############################################


##############################################
##############################################
#                 MAIN                      ##
##############################################
##############################################

def main():
    # program enable/disable
    progEnDis = ProgEnDis(disableFile=disableFile)

    if parsedArgs.backup_now:
        computeBackups()
    elif parsedArgs.enable:
        progEnDis.progEnable()
    elif parsedArgs.disable:
        progEnDis.progDisable()
    else:
        # be sure that backup is not running
        if not(os.path.isfile(runningFile)):
            # Be sure that it has not been already launched today
            # and that it's the good time to launch it 3h < x < 4h
            if not alreadyLaunchedToday() and inGoodTime() :
                # create configFile with today date
                createCfgFile()

                if progEnDis.isEnable():
                    # create a specific file to indicate program is running
                    open(runningFile, "w")
                    # shutdown screens to reduce power consuming
                    screenOff()
                    # compute backups
                    computeBackups()
                    # power up screens
                    screenOn()
                    # program the next wake
                    computeWake()
                    # delete the working specific file
                    if os.path.isfile(runningFile):
                        os.remove(runningFile)


if __name__ == '__main__':
    main()
