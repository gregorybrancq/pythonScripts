#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
To use computer when it is not used, make the backup during the night.
It will compute the different backups configuration, turn off/on screens to reduce power consumption.

To power up computer when it is in sleep mode :
https://forum.ubuntu-fr.org/viewtopic.php?id=1992493
"""

import os
import subprocess
import sys
import datetime
from optparse import OptionParser

sys.path.append('../pythonCommon')
from progDisEn import ProgEnDis
from basic import sendMail


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
runningFile = os.path.join("/tmp", progName + ".running")
disableFile = os.path.join("/tmp", progName + ".disable")

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
        #self.cfgs["home"] = Backup(periods=["yearly", "monthly", "weekly", "daily"], cfgFile="/home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf")
        self.cfgs["vps"] = Backup(periods=["yearly", "monthly", "weekly", "daily"], cfgFile="/home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf")

    def run(self):
        for cfg in self.cfgs.keys():
            self.cfgs[cfg].run()

# Backup Home
#retain	daily	7
#retain	weekly	5
#retain	monthly	6
#retain	yearly	4
#
#30 12   *   *   *    nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf daily 2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Home : daily"  gregory.brancq@free.fr
#20 12   *   *   1    nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf weekly  2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Home : weekly" gregory.brancq@free.fr
#10 12  1-7  *   *    [ "$(date '+\%u')" -eq 1 ] && nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf monthly 2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Home : monthly" gregory.brancq@free.fr
#00 12  1-7 1,4,8,12  *    [ "$(date '+\%u')" -eq 1 ] && nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf yearly 2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Home : yearly" gregory.brancq@free.fr

# Backup Vps
#retain	daily	7
#retain	weekly	5
#retain	monthly	6
#retain	yearly	4
#
#30 18   *   *   *    nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf daily 2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Vps : daily"  gregory.brancq@free.fr
#20 18   *   *   1    nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf weekly  2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Vps : weekly" gregory.brancq@free.fr
#10 18  1-7  *   *    [ "$(date '+\%u')" -eq 1 ] && nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf monthly 2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Vps : monthly" gregory.brancq@free.fr
#00 18  1-7 1,4,8,12  *    [ "$(date '+\%u')" -eq 1 ] && nice /usr/bin/rsnapshot -c /home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf yearly 2>&1 | /usr/local/bin/rsnapreport.pl | mail -s "Rsnapshot Vps : yearly" gregory.brancq@free.fr


class Backup:
    def __init__(self, periods, cfgFile):
        self.periods = periods
        self.cfg = cfgFile
        self.cmd = str()

    def __str__(self):
        res = str()
        res += "  config file = " + self.cfg + "\n"
        res += "  periods     = " + str(self.periods) + "\n"
        return res

    def run(self):
        cmd = str()
        for period in self.periods:
            periodC = Period(period)
            if periodC.canBeLaunch() :
                cmd += "/usr/bin/rsnapshot -c " +  self.cfg + " " + period
                #cmd += "| /usr/local/bin/rsnapreport.pl "
                #cmd += "| mail -s 'Rsnapshot Vps : " + period + "' gregory.brancq@free.fr"
                cmdL = cmd.split(" ")
                if parsedArgs.dry_run:
                    print("Command to launch :\n" + cmd)
                else:
                    proc = subprocess.Popen(cmdL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    proc.wait()
                    res = proc.communicate()
                    msg = res[0]
                    err = res[1]
                    print("Message = " + msg)
                    print("Error   = " + err)
                    if proc.returncode == 0 :
                        sendMail(From="gregory.brancq@free.fr", To="gregory.brancq@free.fr",
                                 Subject="Rsnapshot Vps : " + period, MessageText="No error with backup : \nMessage = "
                                        "\n" + str(msg) + "\nError = \n" + str(err))
                    else :
                        sendMail(From="gregory.brancq@free.fr", To="gregory.brancq@free.fr",
                                 Subject="Rsnapshot Vps : " + period, MessageText="Error with backup : \nMessage = "
                                        "\n" + str(msg) + "\nError = \n" + str(err))


class Period:

    def __init__(self, periodName):
        self.curDay = datetime.datetime.now().weekday()
        self.curDate = datetime.datetime.now().day
        self.curMonth = datetime.datetime.now().month
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

def computeBackups():
    backups = Backups()
    if parsedArgs.dry_run:
        print(str(backups))
    backups.run()

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
    # to wakeup computer
    #echo 0 > /sys/class/rtc/rtc0/wakealarm && date '+%s' -d '+ 1 minutes' > /sys/class/rtc/rtc0/wakealarm
    # to check
    #grep 'al\|time' < /proc/driver/rtc
    # once it's done, you have to reprogram it

    # be sure that backup is not running
    if not(os.path.isfile(runningFile)):
        # create a specific file to indicate program is running
        open(runningFile, "w")

        # program enable/disable
        progEnDis = ProgEnDis(disableFile=disableFile)

        if parsedArgs.backup_now:
            computeBackups()
        elif parsedArgs.enable:
            progEnDis.setEnable()
        elif parsedArgs.disable:
            progEnDis.setDisable()
        else:
            if progEnDis.isEnable():
                # shutdown screens to reduce power consuming
                #screenOff() TODO reactivate
                # compute backups
                computeBackups()
                # power up screens
                #screenOn()

        # delete the working specific file
        if os.path.isfile(runningFile):
            os.remove(runningFile)


if __name__ == '__main__':
    main()
