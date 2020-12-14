#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rsync firefox and thunderbird data from portable to home computer.
"""
import os
import subprocess
import sys

sys.path.append('/home/greg/Config/env/pythonCommon')
from basic import getConfigDir
from log_and_parse import createLog, parsingLine
from program import Program
from network import checkAddress, getIp

##############################################
# Global variables
##############################################

progName = 'rsyncData'

# data
data = "/media/perso/data/"
remote = "greg@home:"

# flag
error = False
pc = None


##############################################
# Functions
##############################################

def rsyncData(param):
    global error
    src = param[0]
    dst = param[1]
    logger.info("RsyncData from %s to %s" % (src, dst))

    # construct command
    cmd = 'rsync -rulpgvz --delete -e '
    if pc == "Portable":
        cmd += '"ssh -p 2832" '
    cmd += src + ' ' + dst

    logger.info("RsyncData cmd = %s" % str(cmd))
    if not parsedArgs.dryRun :
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True)
        proc.wait()
        if proc.returncode != 0:
            error = True
            logger.error("Error during rsync data from %s to %s" % (src, dst))


def getDirName(tool):
    """ get the directories names of source and target"""
    tool_source = os.path.join(data, tool, pc, "*")
    tool_target = str()
    if pc == "Portable":
        tool_target += remote
    tool_target += os.path.join(getConfigDir(), tool, pc)
    logger.debug("tool_source = %s, tool_target = %s" % (tool_source, tool_target))
    return tool_source, tool_target


def copyLocalData():
    """ copy local data to home directory """
    logger.info("Copy thunderbird data")
    rsyncData(getDirName("thunderbird"))

    logger.info("Copy firefox data")
    rsyncData(getDirName("firefox"))


def main():
    global pc
    logger.info("START")

    # determine on which pc this program is launched
    my_ip = getIp()
    if my_ip == "192.168.1.101":
        pc = "Home"
    elif my_ip == "192.168.1.103":
        pc = "Portable"
    else:
        logger.exit("Can't determine the pc.")
        sys.exit(1)

    # config file name
    config_file = os.path.join(getConfigDir(), progName, progName + "_" + pc + ".cfg")

    # program management
    program = Program(prog_name=progName, config_file=config_file)

    # be sure that synchronisation is not running
    if not program.isRunning():
        program.startRunning()
        # be sure that it has not been already launched today
        if not program.isLaunchedToday():
            # Check if home computer is power on and accessible
            if checkAddress("192.168.1.101"):
                # Rsync local data
                copyLocalData()
                if not error and not parsedArgs.dryRun:
                    # Update config file
                    program.runToday()
        program.stopRunning()

    logger.info("STOP\n")


if __name__ == '__main__':
    # Create log class
    (parsedArgs, args) = parsingLine()
    logger = createLog(progName, parsedArgs)

    main()
