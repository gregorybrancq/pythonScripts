#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
To use computer when it is not used, make the backup during the night.
It computes the different backups configuration, and turn off/on screens to reduce power consumption.
"""

import logging
import os
import smtplib
import subprocess
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

sys.path.append('/home/greg/Greg/work/env/pythonCommon')
from progDisEn import ProgEnDis
from mail import sendMail
from basic import getLogDir, getConfigDir

##############################################
# Global variables
##############################################

progName = "backupNight"
userMail = "gregory.brancq@free.fr"

# when the computer will wake up
wakeUpHour = 3

# configuration files
configFile = os.path.join(getConfigDir(), progName, progName + ".cfg")
runningFile = os.path.join("/tmp", progName + ".running")
disableFile = os.path.join("/tmp", progName + ".disable")

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
    help="Just print what it does."
)

parser.add_option(
    "-e",
    "--enable",
    action="store_true",
    dest="enable",
    default=False,
    help="Enable automatic backup behavior."
)

parser.add_option(
    "-d",
    "--disable",
    action="store_true",
    dest="disable",
    default=False,
    help="Disable this program for one night."
)

(parsed_args, args) = parser.parse_args()


##############################################


##############################################
# Class
##############################################

class Backups:
    def __init__(self):
        self.cfgs = dict()
        self.add_backup_config()

    def __str__(self):
        res = str()
        for cfg in self.cfgs.keys():
            res += "Config " + cfg + "\n"
            res += str(self.cfgs[cfg])
        return res

    def add_backup_config(self):
        self.cfgs["home"] = Backup(name="Home", periods=["yearly", "monthly", "weekly", "daily"],
                                   cfg_file="/home/greg/Greg/work/config/rsnapshot/rsnapshot_home.conf")
        self.cfgs["vps"] = Backup(name="Vps", periods=["yearly", "monthly", "weekly", "daily"],
                                  cfg_file="/home/greg/Greg/work/config/rsnapshot/rsnapshot_vps.conf")

    def run(self):
        for cfg in self.cfgs.keys():
            self.cfgs[cfg].run()


class Backup:
    def __init__(self, name, periods, cfg_file):
        self.name = name
        self.periods = periods
        self.cfg = cfg_file
        self.cmd = str()

    def __str__(self):
        res = str()
        res += "  config file = " + self.cfg + "\n"
        res += "  periods     = " + str(self.periods) + "\n"
        return res

    def run(self):
        for period in self.periods:
            logger.debug("In  Backup %s, run period=%s" % (self.name, str(period)))
            period_class = Period(period)
            if period_class.canBeLaunch():
                if period == "weekly":
                    syncLocalData()

                cmd = ["/usr/bin/rsnapshot", "-c", self.cfg, period]
                if parsed_args.dry_run:
                    logger.info("In  Backup run %s cmd=%s" % (str(period), str(cmd)))
                else:
                    logger.info("In  Backup run %s cmd=%s" % (str(period), str(cmd)))
                    process_backup = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    res = process_backup.communicate()
                    msg = res[0]
                    err = res[1]
                    message_bytes = b'\n\nMessage log :\n\n' + msg
                    if err != "":
                        message_bytes = b'\n\nError log : \n\n' + err + message_bytes
                    message_string = message_bytes.decode()
                    logger.debug("In  Backup returnCode=%s, msg=%s, err=%s" % (
                        str(process_backup.returncode), str(msg), str(err)))
                    if process_backup.returncode == 0:
                        if period == "daily":
                            process_report = subprocess.Popen(["/usr/local/bin/rsnapreport.pl"],
                                                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                              stderr=subprocess.PIPE)
                            out_report = process_report.communicate(input=msg)[0]
                            logger.info("In  Backup daily sendmail out_report=%s" % str(out_report.decode()))
                            try:
                                sendMail(from_user=userMail, to_user=userMail,
                                         subject="Rsnapshot " + self.name + " : " + period,
                                         message=out_report.decode() + message_string)
                            except smtplib.SMTPSenderRefused:
                                # if message is too high to be sent by mail
                                sendMail(from_user=userMail, to_user=userMail,
                                         subject="Rsnapshot " + self.name + " : " + period,
                                         message=out_report)
                        else:
                            logger.info("In  Backup not daily sendmail")
                            sendMail(from_user=userMail, to_user=userMail,
                                     subject="Rsnapshot " + self.name + " : " + period,
                                     message=message_string)
                    else:
                        logger.info("In  Backup error")
                        sendMail(from_user=userMail, to_user=userMail,
                                 subject="Error Rsnapshot " + self.name + " : " + period,
                                 message=message_string)


class Period:

    def __init__(self, name):
        self.curDay = datetime.now().weekday()
        self.curDate = datetime.now().day
        self.curMonth = datetime.now().month
        self.period = name
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

def createLog(log_name):
    global logger
    # Create logger
    if not os.path.isdir(getLogDir()):
        os.mkdir(getLogDir())
    # create logger
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    # fh = logging.FileHandler(os.path.join('log', '%s.log' % log_name))
    fh = RotatingFileHandler(os.path.join(getLogDir(), '%s.log' % log_name), mode='a', maxBytes=5 * 1024 * 1024,
                             backupCount=2, delay=False)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(name)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    if parsed_args.debug:
        logger.addHandler(ch)
    return logger


# Check that it's the good time to launch
def inGoodTime():
    cur_hour = datetime.now().hour
    # Relative to when the computer must be wake up
    # be careful between utc and local time.
    if wakeUpHour <= cur_hour < wakeUpHour + 1:
        logger.debug("In  inGoodTime True cur_hour=" + str(cur_hour))
        return True
    logger.info("In  inGoodTime False cur_hour=" + str(cur_hour))
    return False


def alreadyLaunchedToday():
    if not os.path.isfile(configFile):
        logger.info("In  alreadyLaunchedToday no configFile")
        return False
    else:
        fd = open(configFile, 'r')
        date_file_str = fd.read().rstrip('\n')
        try:
            config_date = datetime.strptime(date_file_str, "%Y-%m-%d")
        except ValueError:
            logger.debug("In  alreadyLaunchedToday config_date valueError")
            return True
        current_dt = datetime.now().date()
        if config_date == current_dt:
            logger.debug("In  alreadyLaunchedToday config_date=current_dt")
            return True
        logger.info(
            "In  alreadyLaunchedToday config_date (%s) != current_dt (%s)" % (str(config_date), str(current_dt)))
        return False


def createCfgFile():
    if os.path.isfile(configFile):
        logger.debug("In  createCfgFile remove file")
        os.remove(configFile)
    logger.debug("In  createCfgFile create file")
    fd = open(configFile, 'w')
    fd.write(str(datetime.now().date()))
    fd.close()
    os.chown(configFile, 1000, 1000)


def computeBackups():
    backups = Backups()
    if parsed_args.dry_run:
        print(str(backups))
    backups.run()


def programNextWakeUp():
    logger.info("In  programNextWakeUp")
    # to wakeup computer
    # echo 0 > /sys/class/rtc/rtc0/wakealarm && date '+%s' -d '+ 1 minutes' > /sys/class/rtc/rtc0/wakealarm
    # to check
    # grep 'al\|time' < /proc/driver/rtc
    # this is utc time, so minus 1 during winter, and minus 2 during summer
    cmd = 'echo 0 > /sys/class/rtc/rtc0/wakealarm && date -u --date "Tomorrow ' + str(wakeUpHour - 2) \
          + ':01:00" +%s  > /sys/class/rtc/rtc0/wakealarm '
    os.system(cmd)


def rsyncData(src, dst):
    print("  " + src + " to " + dst)
    cmd = "rsync -rulpgvz --delete "
    cmd += src + " " + dst
    process_sync = subprocess.Popen(cmd, shell=True)
    process_sync.wait()
    if process_sync.returncode != 0:
        print("Error during rsync data")


def syncLocalData():
    # copy local data to config directory
    logger.info("Copy thunderbird data")
    rsyncData("/media/perso/data/thunderbird/*", "/home/greg/Greg/work/config/thunderbird/Home")

    logger.info("Copy firefox data")
    rsyncData("/media/perso/data/firefox/*", "/home/greg/Greg/work/config/firefox/Home")


def screenOn():
    logger.info("Power on screens")
    subprocess.call(["xset", "dpms", "force", "on"])


def screenOff():
    logger.info("Power off screens")
    subprocess.call(["xset", "dpms", "force", "off"])


##############################################


##############################################
##############################################
#                 MAIN                      ##
##############################################
##############################################

def main():
    logger.info("START")

    # program enable/disable
    enable_disable = ProgEnDis(disable_file=disableFile)

    if parsed_args.backup_now:
        # compute backup now
        computeBackups()
    elif parsed_args.enable:
        # enable automatic backup
        enable_disable.progEnable()
    elif parsed_args.disable:
        # disable the program for one night
        enable_disable.progDisable()
    else:
        # be sure that backup is not running
        if not (os.path.isfile(runningFile)):
            logger.info("In  main, runningFile is not present")
            # Be sure that it has not been already launched today
            # and that it's the good time to launch it 3h < x < 4h
            if not alreadyLaunchedToday() and inGoodTime():
                logger.debug("In  main, in good time and not launched today")
                if enable_disable.isEnable():
                    logger.debug("In  main isEnable")
                    # create a specific file to indicate program is running
                    logger.debug("In  main, create running file")
                    open(runningFile, "w")
                    # shutdown screens to reduce power consuming
                    screenOff()
                    # compute backups
                    computeBackups()
                    # power up screens
                    screenOn()
                    if not parsed_args.dry_run:
                        # program the next wake up
                        programNextWakeUp()
                        # create configFile with today date
                        createCfgFile()
                    # delete the working specific file
                    if os.path.isfile(runningFile):
                        logger.info("In  main, remove running file")
                        os.remove(runningFile)

    logger.info("STOP")


if __name__ == '__main__':
    logger = createLog(progName)
    main()
