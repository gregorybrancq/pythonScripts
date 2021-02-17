#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
To make backup tasks automatically in background.
It computes the different backups configuration, and can turn off/on screens to reduce power consumption.

The cron command to launch it the first monday of the month at 10:03 :
3   10  1-7 *   *   [ "$(date '+\%u')" = "1" ] &&
                        export DISPLAY=:0.0 &&
                        nice +10 /home/greg/Config/env/bin/backupInternalDisk

and to be sure that computer will wake up, you can add :
#0   12  *   *   *    export DISPLAY=:0.0 &&
                echo 0 > /sys/class/rtc/rtc0/wakealarm &&
                 date --date "First monday month 10:00:00" +\%s  > /sys/class/rtc/rtc0/wakealarm
"""
import os
import subprocess
import sys
from datetime import datetime
from optparse import OptionParser

sys.path.append('/home/greg/Config/env/pythonCommon')
from program import Program
from mail import SendMail
from basic import getToolsDir
from log import LogClass
from message import KillQuestionAfterDelay
from shell_commands import suspendComputer

##############################################
# Global variables
##############################################

prog_name = "backupInternalDisk"

# when the computer will wake up
wakeUpHour = 10

# configuration files
config_file = os.path.join(getToolsDir(), prog_name, prog_name + ".cfg")
rsnapshotFocus = os.path.join(getToolsDir(), "rsnapshot", "rsnapshot_focus.conf")
rsyncFocus = os.path.join(getToolsDir(), "grsync", "videos.filter")
# rsnapshotQuantum = os.path.join(getToolsDir(), "rsnapshot", "rsnapshot_quantum.conf")

##############################################
#              Line Parsing                 ##
##############################################

parser = OptionParser()

parser.add_option(
    "--debug",
    action="store_true",
    dest="debug",
    default=False,
    help="Display all debug information."
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
        self.configs = dict()

    def __str__(self):
        res = str()
        for config in self.configs.keys():
            res += "Config " + config + "\n"
            res += str(self.configs[config])
        return res

    def add_backup_config(self):
        self.configs["focus_data"] = Backup(name="Focus_data", periods=["yearly", "monthly"],
                                            tool="rsnapshot", cfg_file=rsnapshotFocus)
        self.configs["focus_video"] = Backup(name="Focus_video", periods=["yearly", "monthly"],
                                             tool="rsync", cfg_file=rsyncFocus)
        # self.configs["quantum"] = Backup(name="Quantum", periods=["yearly", "monthly", "weekly", "daily"],
        #                           tool="rsnapshot", cfg_file=rsnapshotQuantum)

    def run(self):
        self.add_backup_config()
        if parsed_args.dry_run:
            print(str(self))
        for cfg in self.configs.keys():
            self.configs[cfg].run()


class Backup:
    def __init__(self, name, periods, tool, cfg_file):
        self.name = name
        self.periods = periods
        self.tool = tool
        self.cfg = cfg_file
        self.cmd = str()

    def __str__(self):
        res = str()
        res += "  tool        = " + self.tool + "\n"
        res += "  config file = " + self.cfg + "\n"
        res += "  periods     = " + str(self.periods) + "\n"
        return res

    def run(self):
        for period in self.periods:
            period_class = Period(period)
            if period_class.canBeLaunch():
                cmd = list()
                if self.tool == "rsnapshot":
                    cmd = ["/usr/bin/rsnapshot", "-c", self.cfg, period]
                elif self.tool == "rsync":
                    # add -n option to dry-run
                    cmd = ["/usr/bin/rsync", "-r", "-t", "-p", "-o", "-g", "-v",
                           "--progress", "--delete", "-l", "-b", "--delete-excluded",
                           "--delete-before", "--ignore-errors", "--filter=. " + self.cfg,
                           "/home/greg/Vidéos/", "/media/backup/video"]

                logger.info("Backup %s run %s cmd='%s'" % (self.name, str(period), str(" ".join(cmd))))
                if not parsed_args.dry_run:
                    process_backup = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    res = process_backup.communicate()
                    detail = res[0]
                    msg = res[1]

                    # analyse
                    if process_backup.returncode != 0:
                        logger.error("Backup failed.\nError with command %s\n\nMessage :\n%s"
                                     % (str(" ".join(cmd)), msg.decode('utf-8', errors="ignore")))
                        mail.send(subject="Backup failed.\nError with command '%s'" % (str(" ".join(cmd))),
                                  message="See log file %s\nSee config file %s\n\nMessage :\n%s"
                                          % (logC.getLogFile(), config_file, msg.decode('utf-8', errors="ignore")),
                                  code=2)

                        program.stopRunning()
                        sys.exit(1)
                    else:
                        # for rsnapshot, parse output report to be more readable
                        if self.tool == "rsnapshot" and process_backup.returncode == 0:
                            process_report = subprocess.Popen(["/usr/local/bin/rsnapreport.pl"],
                                                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                              stderr=subprocess.PIPE)
                            out_report = process_report.communicate(input=res[0])[0]
                            logger.info("Rsnapshot report : \n%s" % out_report.decode('utf-8', errors="ignore"))

                        logger.info("Program output : \n%s" % msg.decode('utf-8', errors="ignore"))
                        logger.debug("Program detail : \n%s" % detail.decode('utf-8', errors="ignore"))

                        if not parsed_args.dry_run:
                            # program the next wake up
                            programNextWakeUp()
                            # Update config file
                            program.runToday()


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


def programNextWakeUp():
    logger.info("In  programNextWakeUp")
    # to wakeup computer
    # echo 0 > /sys/class/rtc/rtc0/wakealarm && date '+%s' -d '+ 1 minutes' > /sys/class/rtc/rtc0/wakealarm
    # to check
    # grep 'al\|time' < /proc/driver/rtc
    # this is utc time, so to avoid to precise minus 1 during winter, and minus 2 during summer
    # specify timezone
    cmd = 'echo 0 > /sys/class/rtc/rtc0/wakealarm && date -u --date=' + "'" + \
          'TZ="Europe/Paris" First monday month ' + str(wakeUpHour) + \
          ':00:00' + "' +%s > /sys/class/rtc/rtc0/wakealarm"
    logger.debug("In  programNextWakeUp cmd=" + str(cmd))
    os.system(cmd)
    logger.info("Out programNextWakeUp")


##############################################


##############################################
##############################################
#                 MAIN                      ##
##############################################
##############################################

def main():
    # check if backup is not currently running
    if not program.isRunning():
        program.startRunning()

        if parsed_args.enable:
            # enable automatic backup
            program.progEnable()
        elif parsed_args.disable:
            # disable the program
            program.progDisable()
        else:
            # check if it has not already been launched
            if parsed_args.backup_now or (
                    not program.isLaunchedLastDays(days=20) and inGoodTime() and program.isEnable()):
                # shutdown screens to reduce power consuming
                # screenPower(False)
                # compute backups
                backups = Backups()
                backups.run()
                # power up screens
                # screenPower(True)

        program.stopRunning(stop_program=False)

    # be sure that synchronisation is not locked by another process
    if not program.isLaunchedLastDays(days=60):
        mail.send(subject="Not launched since more than 60 days",
                  message="See log file %s\nSee config file %s" % (logC.getLogFile(), config_file),
                  code=1)

    program.stopLog()

    # put the computer in suspend mode
    if not parsed_args.dry_run:
        answer = KillQuestionAfterDelay(300, "Veux-tu que l'ordinateur passe en mode veille ?",
                                        "si tu cliques oui, l'ordinateur va s'éteindre...").run()
        if answer:
            suspendComputer()


if __name__ == '__main__':
    logC = LogClass(prog_name, parsed_args.debug)
    logger = logC.getLogger()
    mail = SendMail(prog_name=prog_name)
    program = Program(prog_name=prog_name, config_file=config_file)
    main()
