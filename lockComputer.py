#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging.config
import os
import os.path
import subprocess
import sys
import time
from datetime import datetime, timedelta
from optparse import OptionParser

# common
sys.path.append('..')
from pythonCommon.color import *
from pythonCommon.basic import getScriptDir, getLogDir
import pythonCommon.log

progName = "lockComputer"

##############################################


##############################################
##############################################
#              Line Parsing                 ##
##############################################
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
    "-b",
    "--block",
    action="store_true",
    dest="block",
    default=False,
    help="Block keyboard and mouse."
)

parser.add_option(
    "-u",
    "--unblock",
    action="store_true",
    dest="unblock",
    default=False,
    help="Unblock keyboard and mouse."
)

parser.add_option(
    "-e",
    "--enable",
    action="store_true",
    dest="enable",
    default=False,
    help="Block and unblock keyboard and mouse depending time part."
)

parser.add_option(
    "-d",
    "--disable",
    action="store_true",
    dest="disable",
    default=False,
    help="Disable this program."
)

parser.add_option(
    "-t",
    "--time",
    action="store_true",
    dest="timeUser",
    default=False,
    help="Display time user."
)

(parsedArgs, args) = parser.parse_args()

##############################################


##############################################
# Global variables
##############################################

# directory
scriptDir = getScriptDir()
logDir = getLogDir()

# logging
# load config
logging.config.fileConfig(os.path.join(scriptDir, 'logging.conf'))
# disable logging
logging.disable(sys.maxsize)
# create logger
log = logging.getLogger(progName)

logFile = os.path.join(logDir, progName + "_"
                       + str(datetime.today().isoformat("_") + ".log"))

# True will suspend pc

# Holidays
# userSlot = [
#    ["lundi",    {"01:00": True, "06:00": False}],
#    ["mardi",    {"01:00": True, "06:00": False}],
#    ["mercredi", {"01:00": True, "06:00": False}],
#    ["jeudi",    {"01:00": True, "06:00": False}],
#    ["vendredi", {"01:00": True, "06:00": False}],
#    ["samedi",   {"02:00": True, "06:00": False}],
#    ["dimanche", {"02:00": True, "06:00": False}]
# ]

# Work week
userSlot = [
    ["lundi", {"00:00": True, "06:00": False, "23:45": True}],
    ["mardi", {"00:00": True, "06:00": False, "23:45": True}],
    ["mercredi", {"00:00": True, "06:00": False, "23:45": True}],
    ["jeudi", {"00:00": True, "06:00": False, "23:45": True}],
    ["vendredi", {"00:00": True, "06:00": False}],
    ["samedi", {"00:00": False, "02:00": True, "07:00": False}],
    ["dimanche", {"00:00": False, "02:00": True, "07:00": False, "23:45": True}]
]

##############################################


##############################################
##############################################
#                  CLASS                    ##
##############################################
##############################################

class HardwareElements:
    def __init__(self):
        self.hardwareList = list()

    def __str__(self):
        res = str()
        i = 1
        for hardware in self.hardwareList:
            res += "## Hardware " + str(i) + "\n"
            res += str(hardware) + "\n"
            i += 1
        return res

    def init(self, *hardwares):
        for hardware in hardwares:
            hardwareC = Hardware(hardware[0], hardware[1])
            self.hardwareList.append(hardwareC)

    def block(self):
        for hardware in self.hardwareList:
            hardware.block()

    def unblock(self):
        for hardware in self.hardwareList:
            hardware.unblock()


class Hardware:
    def __init__(self, name, fullName):
        self.short = name
        self.full = fullName
        self.id = int()
        self.getId()

    def __str__(self):
        res = str()
        res += "#    name = " + str(self.short) + "\n"
        res += "#    full = " + str(self.full) + "\n"
        res += "#    id   = " + str(self.id)
        return res

    def getId(self):
        try:
            self.id = subprocess.check_output(["xinput", "list", "--id-only", str(self.full)]).strip()
        except subprocess.CalledProcessError:
            log.error("In getId : error with " + str(self.short))

    def block(self):
        log.info("In  block " + self.short)
        subprocess.call(["xinput", "disable", str(self.id)])
        log.info("Out block")

    def unblock(self):
        log.info("In  unblock " + self.short)
        subprocess.call(["xinput", "enable", str(self.id)])
        log.info("Out unblock")


class ProgEnDis:
    def __init__(self):
        self.enable = bool()
        self.disableFile = os.path.join("/tmp", progName + ".disable")
        self.justRemoveFile = False
        self.checkDisableFile()

    def __str__(self):
        res = str()
        res += "# disableFile = " + str(self.disableFile) + "\n"
        return res

    # if this program can be launched
    def isEn(self):
        if self.enable:
            return True
        return False

    # if just remove file
    def isJustRemoveFile(self):
        if self.justRemoveFile:
            return True
        return False

    # Enable it
    def enProg(self):
        log.info("In  enProg")
        if os.path.isfile(self.disableFile):
            log.info("Delete disableFile " + str(self.disableFile))
            os.remove(self.disableFile)
            self.justRemoveFile = True
        self.enable = True

    # Disable it
    def disProg(self):
        log.info("In  disProg")
        fd = open(self.disableFile, 'w')
        fd.write(str(datetime.now()))
        fd.close()
        self.enable = False
        self.checkDisableFile()
        log.info("Out disProg")

    # Check file date creation is
    #  return True  if > 1 day
    #  return False if < 1 day
    def checkFileDate(self):
        fd = open(self.disableFile, 'r')
        dateFileStr = fd.read().rstrip('\n')
        dateFileDT = datetime.strptime(dateFileStr, "%Y-%m-%d %H:%M:%S.%f")
        currentDT = datetime.now()
        if dateFileDT + timedelta(days=1) < currentDT:
            log.info("In  checkFileDate file has been created more than 1 day")
            return True
        return False

    # Check if disableFile exists more than one day
    def checkDisableFile(self):
        if not os.path.isfile(self.disableFile):
            log.info("In  checkDisableFile : no disableFile")
            self.enable = True
        else:
            # check if more than one day
            if self.checkFileDate():
                log.info("In  checkDisableFile : more than one day")
                self.enProg()
            else:
                log.info("In  checkDisableFile : less than one day")
                self.enable = False


class TimeSlot:
    def __init__(self):
        self.curDOW = datetime.now().weekday()

    def __str__(self):
        res = str()
        res += "# current day of week = " + str(self.curDOW) + "\n"
        return res

    def sortUserSlot(self):
        userSort = userSlot[self.curDOW][1].keys()
        log.debug("UserTime before sort =" + str(userSort))
        userSort.sort(reverse=True)
        log.debug("UserTime after sort =" + str(userSort))
        return userSort

    # Check if current time + 5mn is in timeSlot defined by user
    def checkBeforeTS(self):
        log.info("Check before time slot")
        curT5 = datetime.now() + timedelta(minutes=4)
        curTime5 = format(curT5, '%H:%M')
        log.debug("Check real time slot curTime5=" + str(curTime5))
        log.debug("Check user times=" + str(userSlot[self.curDOW][1]))
        for userTime in self.sortUserSlot():
            log.debug("Check user time slot userTime=" + str(userTime))
            if curTime5 > userTime:
                return userSlot[self.curDOW][1][userTime]

    # Check if datetime is in timeSlot defined by user
    def inTS(self):
        log.info("Check time slot")
        curTime = time.strftime("%H:%M")
        log.debug("Check real time slot curTime =" + str(curTime))
        log.debug("Check user times=" + str(userSlot[self.curDOW][1]))
        for userTime in self.sortUserSlot():
            log.debug("Check user time slot userTime=" + str(userTime))
            if curTime > userTime:
                return userSlot[self.curDOW][1][userTime]

##############################################


##############################################
##############################################
#                FUNCTIONS                  ##
##############################################
##############################################

def suspend():
    log.info("Suspend machine")
    subprocess.call(["systemctl", "suspend"])


def message():
    log.info("Echo user")
    subprocess.call(['zenity', '--info', '--timeout=300', '--no-wrap',
                     '--text=Il est temps d\'aller faire dodo\nT\'as 5mn avant l\'extinction des feux…'])

##############################################


##############################################
##############################################
##############################################
#                 MAIN                      ##
##############################################
##############################################
##############################################

def main():
    log.info("In  main")

    hardwareElts = HardwareElements()
    # To get the good names : xinput list
    hardwareElts.init(["keyboard", "keyboard:Logitech MK700"],
                      ["mouseJuju", "pointer:MOSART Semi. 2.4G Wireless Mouse"])
    # ["mouseJuju", "pointer:MOSART Semi. 2.4G Wireless Mouse"], \
    # ["mouseHanna", "pointer:Logitech M505/B605"])
    log.debug("Hardwares :\n" + str(hardwareElts))

    progEnDis = ProgEnDis()

    if parsedArgs.block:
        hardwareElts.block()
    elif parsedArgs.unblock:
        hardwareElts.unblock()
    elif parsedArgs.enable:
        progEnDis.enProg()
    elif parsedArgs.disable:
        progEnDis.disProg()
    elif parsedArgs.timeUser:
        for day in userSlot:
            print(str(day))
    else:
        if progEnDis.isEn():
            ts = TimeSlot()
            log.debug("TimeSlot :\n" + str(ts))
            if ts.inTS():
                # when lock file was created after the TS
                # this trick to have the user message
                if progEnDis.isJustRemoveFile():
                    message()
                else:
                    hardwareElts.block()
                    suspend()
            elif ts.checkBeforeTS():
                message()
            else:
                log.info("not in a suspend time slot")
                # hardwareElts.unblock()

    log.info("Out main")


if __name__ == '__main__':
    main()
