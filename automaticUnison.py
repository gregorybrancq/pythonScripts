#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Program to specify automatically which unison configuration to use
Launch the synchronisation
"""

import os
import re
import subprocess
import sys
from optparse import OptionParser

sys.path.append('/home/greg/Tools/env/pythonCommon')
from basic import getConfigDir, getHomeDir
from log import LogClass
from program import Program
from message import MessageDialog
from network import checkAddress, getIp
from mail import SendMail

##############################################
# Global variables
##############################################

prog_name = 'automaticUnison'
config_file = os.path.join(getConfigDir(), prog_name, prog_name + ".cfg")

# IP
ipName = dict()
ipName["192.168.3.2"] = "neuron"
ipName["192.168.3.3"] = "focus"
ipName["192.168.3.14"] = "focus_wifi"
# ipName["10.42.0.1"] = "server_shared_internet"
# ipName["10.13.0.6"] = "server_vpn"
ipName["192.168.3.4"] = "agile"
ipName["192.168.3.15"] = "agile_wifi"
# ipName["192.168.33.29"] = "agile_office"
# ipName["10.42.0.146"] = "portable_shared_internet"

extDisk = "/media/greg/Transcend_600Go"

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

class Unison(object):
    def __init__(self):
        self.config_name = str()

    def getConfig(self):
        # get local IP
        local_ip = getIp()
        logger.debug("Local IP = %s" % str(local_ip))
        local_config = ipName[local_ip]
        logger.debug("Local config = %s" % str(local_config))
        # Remove _wifi to the name
        local_config = re.sub("_wifi", "", local_config)
        logger.debug("Local config after remove _wifi = %s" % str(local_config))

        # get config name to launch
        remote_target = ""
        remote_config = ""
        if re.search("agile", local_config):
            # remote_target = "focus"
            remote_target = "neuron"
        elif re.search("focus", local_config):
            remote_target = "agile"
            # Check if external disk is connected
            if os.path.isdir(extDisk):
                local_config = "external_disk"
                remote_config = "focus"

        for remoteIp in ipName:
            if re.search(remote_target, ipName[remoteIp]):
                if checkAddress(remoteIp):
                    remote_config = ipName[remoteIp]
                    logger.debug("remote IP = %s, remote config = %s" % (str(remoteIp), str(remote_config)))
                    break

        if remote_config == "":
            error_msg = "Can't find Remote IP. Local IP is %s" % local_ip
            logger.error(error_msg)
            if not parsed_args.nogui:
                MessageDialog(dialog_type='error', title="Automatic Synchronisation",
                              message1=error_msg).run()

            program.stopRunning()
            sys.exit(1)
        else:
            self.config_name = local_config + "-to-" + remote_config + ".prf"
            logger.info("config name to use : %s" % self.config_name)

    def runSync(self):
        logger.debug("RunSync config_name = %s" % self.config_name)
        unison_file = os.path.join(getHomeDir(), ".unison", self.config_name)

        if not os.path.isfile(unison_file):
            error_msg = "Unison config file %s doesn't exist." % unison_file
            logger.error(error_msg)
            if not parsed_args.nogui:
                MessageDialog(dialog_type='error', title="Automatic Synchronisation",
                              message1=error_msg).run()

            program.stopRunning()
            sys.exit(1)

        else:
            if parsed_args.nogui:
                cmd = ["unison", self.config_name]
            else:
                cmd = ["unison-gtk", self.config_name]

            if parsed_args.dry_run:
                logger.info("Dry-run : run sync with command %s" % str(" ".join(cmd)))
            else:
                # run synchronisation
                logger.info("Run synchronisation with command '%s'" % str(" ".join(cmd)))
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res = proc.communicate()
                detail = res[0]
                msg = res[1]

                # analyse
                if proc.returncode != 0:
                    logger.error("Synchronisation failed.\nError with command %s\n\nMessage :\n%s"
                                 % (str(" ".join(cmd)), msg.decode('utf-8', errors="ignore")))
                    mail.send(subject="Synchronisation failed with command '%s'" % str(" ".join(cmd)),
                              message="See log file %s\nSee config file %s\n\nMessage :\n%s"
                                      % (logC.getLogFile(), config_file, msg.decode('utf-8', errors="ignore")),
                              code=2)

                    program.stopRunning()
                    sys.exit(1)
                else:
                    logger.info("Program output : \n%s" % msg.decode('utf-8', errors="ignore"))
                    logger.debug("Program detail : \n%s" % detail.decode('utf-8', errors="ignore"))
                    if not parsed_args.dry_run:
                        # Update config file
                        program.runToday()


def main():
    # check if synchronisation is not currently running
    if not program.isRunning():
        program.startRunning()

        # check if it has not already been launched today
        if not program.isLaunchedLastDays(days=1):
            unison = Unison()
            # get configuration to launch
            unison.getConfig()
            # run synchronisation
            unison.runSync()

        program.stopRunning(stop_program=False)

    # be sure that synchronisation is launched regularly
    if not program.isLaunchedLastDays(days=7):
        mail.send(subject="Not launched since more than 7 days",
                  message="See log file %s\nSee config file %s" % (logC.getLogFile(), config_file),
                  code=1)

    program.stopLog()


if __name__ == '__main__':
    logC = LogClass(prog_name, parsed_args.debug)
    logger = logC.getLogger()
    mail = SendMail(prog_name=prog_name)
    program = Program(prog_name=prog_name, config_file=config_file)
    main()
