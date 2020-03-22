#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
To use computer when it is not used, make the backup during the night.
It will compute the different backups configuration, turn off/on screens to reduce power consumption.

"""
import os
import smtplib
import subprocess
import sys
import logging.config
from datetime import datetime
from optparse import OptionParser

sys.path.append('/home/greg/Greg/work/env/pythonCommon')
from progDisEn import ProgEnDis
from mail import sendMail
from basic import getScriptDir, getLogDir

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

# when the computer will wake up
wakeUpHour = 3

# directory
scriptDir = getScriptDir()
logDir = getLogDir()

# load config
logging.config.fileConfig(os.path.join(scriptDir, 'logging.conf'))
# disable logging
# logging.disable(sys.maxsize)
# create logger
log = logging.getLogger(progName)

logFile = os.path.join(logDir, progName + "_"
                       + str(datetime.today().isoformat("_") + ".log"))

configFile = os.path.join("/home/greg/Greg/work/config", progName, progName + ".cfg")
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
            log.info("In  Backup run period=" + str(period))
            periodC = Period(period)
            if periodC.canBeLaunch():
                log.info("In  Backup run can be launch")
                cmd = ["/usr/bin/rsnapshot", "-c", self.cfg, period]
                if parsedArgs.dry_run:
                    print("Command to launch :\n" + str(cmd))
                else:
                    log.info("In  Backup run procBackup=" + str(cmd))
                    procBackup = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    res = procBackup.communicate()
                    msg = res[0]
                    log.info("In  Backup msg=" + str(msg))
                    err = res[1]
                    log.info("In  Backup err=" + str(err))
                    log.info("In  Backup returnCode=" + str(procBackup.returncode))
                    if procBackup.returncode == 0:
                        if period == "daily":
                            procParsed = subprocess.Popen(["/usr/local/bin/rsnapreport.pl"],
                                                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                          stderr=subprocess.PIPE)
                            outReport = procParsed.communicate(input=msg)[0]
                            log.info("In  Backup daily sendmail outReport=" + str(outReport))
                            try :
                                sendMail(From=userMail, To=userMail,
                                         Subject="Rsnapshot " + self.name + " : " + period,
                                         Message=outReport + "\n\nMessage log :\n" + msg + "\n\nError log : \n" + err)
                            except smtplib.SMTPSenderRefused:
                                sendMail(From=userMail, To=userMail,
                                         Subject="Rsnapshot " + self.name + " : " + period,
                                         Message=outReport)
                        else:
                            log.info("In  Backup not daily sendmail")
                            sendMail(From=userMail, To=userMail,
                                     Subject="Rsnapshot " + self.name + " : " + period,
                                     Message="Message log :\n" + msg + "\n\nError log : \n" + err)
                    else:
                        log.info("In  Backup error")
                        sendMail(From=userMail, To=userMail,
                                 Subject="Error Rsnapshot " + self.name + " : " + period,
                                 Message="Error log : \n" + err + "\n\nMessage log :\n" + msg)
            log.info("Out Backup run")


class Period:

    def __init__(self, periodName):
        self.curDay = datetime.now().weekday()
        self.curDate = datetime.now().day
        self.curMonth = datetime.now().month
        self.period = periodName
        self.level = str()
        self.cmd = str()

    def canBeLaunch(self):
        if self.period == "daily":
            return True
        elif self.period == "weekly":
            if self.curDay == 0:  # monday
                return True
        elif self.period == "monthly":
            if self.curDay == 0:  # monday
                if self.curDate < 8:  # first week of the month
                    return True
        elif self.period == "yearly":
            if self.curDay == 0:  # monday
                if self.curDate < 8:  # first week of the month
                    if self.curMonth == 1 or self.curMonth == 7:  # month : january(=1) or july(=7)
                        return True
        return False


##############################################


##############################################
# Functions
##############################################

# Check that it's the good time to launch
def inGoodTime():
    log.info("In  inGoodTime")
    curHour = datetime.now().hour
    # Relative to when the computer must be wake up
    # be careful between utc and local time.
    if curHour >= wakeUpHour and curHour < wakeUpHour+1:
        log.info("In  inGoodTime True curHour=" + str(curHour))
        return True
    log.info("In  inGoodTime False curHour=" + str(curHour))
    return False


def alreadyLaunchedToday():
    log.info("In  alreadyLaunchedToday")
    if not os.path.isfile(configFile):
        log.info("In  alreadyLaunchedToday no configFile")
        return False
    else:
        log.info("In  alreadyLaunchedToday configFile")
        fd = open(configFile, 'r')
        dateFileStr = fd.read().rstrip('\n')
        try:
            configDate = datetime.strptime(dateFileStr, "%Y-%m-%d")
            log.info("In  alreadyLaunchedToday configDate=" + str(configDate))
        except ValueError:
            log.info("In  alreadyLaunchedToday configDate valueError")
            return True
        currentDT = datetime.now().date()
        log.info("In  alreadyLaunchedToday currentDT=" + str(currentDT))
        if configDate == currentDT:
            log.info("In  alreadyLaunchedToday configDate=currentDT")
            return True
        log.info("In  alreadyLaunchedToday configDate!=currentDT")
        return False


def createCfgFile():
    log.info("In  createCfgFile")
    if os.path.isfile(configFile):
        log.info("In  createCfgFile remove file")
        os.remove(configFile)
    try:
        log.info("In  createCfgFile create file")
        fd = open(configFile, 'w')
        fd.write(str(datetime.now().date()))
        fd.close()
        os.chown(configFile, 1000, 1000)
    except:
        print("Error during configFile creation " + configFile)
    log.info("Out createCfgFile")


def computeBackups():
    log.info("In  computeBackups")
    backups = Backups()
    if parsedArgs.dry_run:
        print(str(backups))
    backups.run()
    log.info("Out computeBackups")


def programNextWakeUp():
    log.info("In  programNextWakeUp")
    # to wakeup computer
    # echo 0 > /sys/class/rtc/rtc0/wakealarm && date '+%s' -d '+ 1 minutes' > /sys/class/rtc/rtc0/wakealarm
    # to check
    # grep 'al\|time' < /proc/driver/rtc
    # this is utc time (so here minus 1)
    cmd = 'echo 0 > /sys/class/rtc/rtc0/wakealarm && date -u --date "Tomorrow ' + str(wakeUpHour-1) \
            + ':00:00" +%s  > /sys/class/rtc/rtc0/wakealarm '
    os.system(cmd)
    log.info("Out programNextWakeUp")


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
    log.info("In  main")
    # program enable/disable
    progEnDis = ProgEnDis(disableFile=disableFile)

    if parsedArgs.backup_now:
        computeBackups()
    elif parsedArgs.enable:
        progEnDis.progEnable()
    elif parsedArgs.disable:
        progEnDis.progDisable()
    else:
        log.info("In  main check if runningFile is not present")
        # be sure that backup is not running
        if not (os.path.isfile(runningFile)):
            log.info("In  main check runningFile is not present")
            # Be sure that it has not been already launched today
            # and that it's the good time to launch it 3h < x < 4h
            if not alreadyLaunchedToday() and inGoodTime():
                log.info("In  main good time and not launched today")
                if progEnDis.isEnable():
                    log.info("In  main isEnable")
                    # create a specific file to indicate program is running
                    log.info("In  main create running file")
                    open(runningFile, "w")
                    # shutdown screens to reduce power consuming
                    screenOff()
                    # compute backups
                    computeBackups()
                    # power up screens
                    screenOn()
                    # program the next wake up
                    programNextWakeUp()
                    # create configFile with today date
                    createCfgFile()
                    # delete the working specific file
                    if os.path.isfile(runningFile):
                        log.info("In  main remove running file")
                        os.remove(runningFile)

    log.info("Out main")


if __name__ == '__main__':
    main()
