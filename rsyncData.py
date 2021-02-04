#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rsync local data to another disk in order to be backuped.
"""
import os
import re
import subprocess
import sys
import socket

sys.path.append('/home/greg/Config/env/pythonCommon')
from basic import getToolsDir
from log_and_parse import createLog, parsingLine
from program import Program

# from network import checkAddress, getIp

##############################################
# Global variables
##############################################

progName = 'rsyncData'
data_dir = "/media/perso/data/"

# flag
error = False
pc_name = None


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
    cmd += src + ' ' + dst

    logger.info("RsyncData cmd = %s" % str(cmd))
    if not parsedArgs.dryRun:
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True)
        proc.wait()
        if proc.returncode != 0:
            error = True
            logger.error("Error during rsync data from %s to %s" % (src, dst))


def getDirName(tool):
    """ get the directories names of source and target"""
    tool_source = os.path.join(data_dir, tool, pc_name, "*")
    tool_target = str()
    tool_target += os.path.join(getToolsDir(), tool, pc_name)

    # check if source exists
    tool_source_wt_star = re.sub("/\*", "", tool_source)
    #logger.debug("tool_source = %s, tool_source_wt_star = %s" % (tool_source, tool_source_wt_star))
    if not os.path.isdir(tool_source_wt_star):
        logger.error("The source doesn't exist : %s" % tool_source_wt_star)
        sys.exit(1)

    # create destination if necessary
    if not os.path.isdir(tool_target):
        os.makedirs(tool_target)

    logger.debug("tool_source = %s, tool_target = %s" % (tool_source, tool_target))
    return tool_source, tool_target


def copyLocalData():
    """ copy local data to home directory """
    logger.info("Copy thunderbird data")
    rsyncData(getDirName("thunderbird"))

    logger.info("Copy firefox data")
    rsyncData(getDirName("firefox"))


def main():
    global pc_name
    logger.info("START")

    pc_name = socket.gethostname()
    # determine on which pc_name this program is launched
    # my_ip = getIp()
    # if my_ip == "192.168.1.101":
    #    pc_name = "Home"
    # elif my_ip == "192.168.1.103":
    #    pc_name = "Portable"
    # else:
    #    logger.error("Can't determine the pc_name.")
    #    sys.exit(1)

    # config file name
    config_file = os.path.join(getToolsDir(), progName, progName + "_" + pc_name + ".cfg")

    # program management
    program = Program(prog_name=progName, config_file=config_file)

    # be sure that synchronisation is not running
    if not program.isRunning():
        program.startRunning()
        # be sure that it has not been already launched today
        if not program.isLaunchedLastDays(days=7):
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
