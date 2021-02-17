#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rsync local data (firefox and thunderbird) to another disk in order to be backuped.
"""
import os
import re
import subprocess
import sys
import socket
from optparse import OptionParser

sys.path.append('/home/greg/Config/env/pythonCommon')
from basic import getToolsDir
from log import LogClass
from program import Program
from mail import SendMail

# from network import checkAddress, getIp

##############################################
# Global variables
##############################################

prog_name = 'rsyncData'
data_dir = "/media/perso/data/"

# flag
pc_name = None

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
    "--nogui",
    action="store_true",
    dest="nogui",
    default=False,
    help="Don't launch GUI."
)

parser.add_option(
    "--dry_run",
    action="store_true",
    dest="dry_run",
    default=False,
    help="Just print what it does."
)

(parsed_args, args) = parser.parse_args()


##############################################


##############################################
# Class
##############################################

class Rsync(object):
    def __init__(self, tool):
        self.tool = tool
        self.source = str()
        self.destination = str()

    def getDirName(self):
        """ get the directories names of source and target"""
        self.source = os.path.join(data_dir, self.tool, pc_name, "*")
        self.destination = str()
        self.destination += os.path.join(getToolsDir(), self.tool, pc_name)

        # check if source exists
        source_wo_star = re.sub("/\*", "", self.source)
        logger.debug("self.source = %s, source_wo_star = %s" % (self.source, source_wo_star))
        if not os.path.isdir(source_wo_star):
            logger.error("For tool %s, source doesn't exist : %s" % (self.tool, source_wo_star))
            program.stopRunning()
            sys.exit(1)

        # create destination if necessary
        if not os.path.isdir(self.destination):
            os.makedirs(self.destination)

    def rsyncData(self):
        # construct command
        cmd = ["/usr/bin/rsync", "-rulpgvz", "--progress", "--delete", "-e",
               self.source, self.destination]

        if parsed_args.dry_run:
            logger.info("Dry-run : rsync data with command = %s" % str(" ".join(cmd)))
        else:
            logger.info("Run synchronisation with command = %s" % str(" ".join(cmd)))
            # run synchronisation
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res = proc.communicate()
            detail = res[0]
            msg = res[1]

            # analyse
            if proc.returncode != 0:
                logger.error("Synchronisation failed.\nError with command %s\n\nMessage :\n%s"
                             % (str(" ".join(cmd)), msg.decode('utf-8', errors="ignore")))
                mail.send(subject="Synchronisation failed with command '%s'" % str(" ".join(cmd)),
                          message="See log file %s\n\nMessage :\n%s"
                                  % (logC.getLogFile(), msg.decode('utf-8', errors="ignore")),
                          code=2)

                program.stopRunning()
                sys.exit(1)
            else:
                logger.info("Program output : \n%s" % msg.decode('utf-8', errors="ignore"))
                logger.debug("Program detail : \n%s" % detail.decode('utf-8', errors="ignore"))

    def run(self):
        self.getDirName()
        self.rsyncData()


def copyLocalData():
    """ copy local data to home directory """
    Rsync("thunderbird").run()
    Rsync("firefox").run()

    if not parsed_args.dry_run:
        # Update config file
        program.runToday()


def main():
    global pc_name
    pc_name = socket.gethostname()

    # config file name
    config_file = os.path.join(getToolsDir(), prog_name, prog_name + "_" + pc_name + ".cfg")
    program.set_config_file(config_file)

    # check if synchronisation is not currently running
    if not program.isRunning():
        program.startRunning()

        # check if it has not already been launched in the last 7 days
        if not program.isLaunchedLastDays(days=7):
            # Rsync local data
            copyLocalData()

        program.stopRunning(stop_program=False)

    # be sure that synchronisation is launched regularly
    if not program.isLaunchedLastDays(days=14):
        mail.send(subject="Not launched since more than 14 days",
                  message="See log file %s\nSee config file %s" % (logC.getLogFile(), config_file),
                  code=1)

    program.stopLog()


if __name__ == '__main__':
    logC = LogClass(prog_name, parsed_args.debug)
    logger = logC.getLogger()
    mail = SendMail(prog_name=prog_name)
    program = Program(prog_name=prog_name)

    main()
