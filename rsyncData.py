#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rsync firefox and thunderbird data from portable to home computer.
"""
import os
import subprocess
import sys

sys.path.append('/home/greg/Greg/work/env/pythonCommon')
from basic import getConfigDir
from log_and_parse import createLog, parsingLine
from program import Program
from network import checkAddress

##############################################
# Global variables
##############################################

progName = 'rsyncData'

# configuration files
configFile = os.path.join(getConfigDir(), progName, progName + ".cfg")

# data
data = "/media/perso/data/"
remote = "greg@home:"
thunderbird_source = os.path.join(data, "thunderbird", "Portable", "*")
thunderbird_target = remote + os.path.join(data, "thunderbird", "Portable")
firefox_source = os.path.join(data, "firefox", "Portable", "*")
firefox_target = remote + os.path.join(data, "firefox", "Portable")

# flag
error = False


##############################################
# Functions
##############################################

def rsyncData(src, dst):
    global error
    logger.debug("RsyncData from %s to %s" % (src, dst))
    cmd = 'rsync -rulpgvz --delete -e "ssh -p 2832" ' + src + ' ' + dst
    logger.debug("RsyncData cmd = %s" % str(cmd))
    proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True)
    proc.wait()
    if proc.returncode != 0:
        error = True
        logger.error("Error during rsync data from %s to %s" % (src, dst))


def copyLocalData():
    """ copy local data to home directory """
    logger.info("Copy thunderbird data from %s to %s" % (thunderbird_source, thunderbird_target))
    rsyncData(thunderbird_source, thunderbird_target)

    logger.info("Copy firefox data from %s to %s" % (firefox_source, firefox_target))
    rsyncData(firefox_source, firefox_target)


def main():
    logger.info("START")

    # program management
    program = Program(prog_name=progName, config_file=configFile)

    # be sure that synchronisation is not running
    if not program.isRunning():
        program.startRunning()
        # be sure that it has not been already launched today
        if not program.isLaunchedToday():
            # Check if home computer is power on and accessible
            if checkAddress("192.168.1.101"):
                # Rsync local data
                copyLocalData()
                if not error:
                    # Update config file
                    program.runToday()
        program.stopRunning()

    logger.info("STOP\n")


if __name__ == '__main__':
    # Create log class
    (parsedArgs, args) = parsingLine()
    logger = createLog(progName, parsedArgs)

    main()
