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

sys.path.append('/home/greg/Config/env/pythonCommon')
from message import MessageDialog
from network import checkAddress, getIp

##############################################
# Global variables
##############################################

ipName = dict()
ipName["192.168.1.101"] = "server"
ipName["192.168.1.102"] = "server_wifi"
ipName["10.42.0.1"] = "server_shared_internet"
ipName["10.13.0.6"] = "server_vpn"
ipName["192.168.1.103"] = "portable"
ipName["192.168.1.104"] = "portable_wifi"
ipName["192.168.33.29"] = "portable_office"
ipName["10.42.0.146"] = "portable_shared_internet"

extDisk = "/media/greg/Transcend_600Go"


##############################################
# Functions
##############################################

def runSync(local_config, remote_config):
    name = local_config + "-to-" + remote_config + "-mode_sata.prf"
    print("Run sync " + name)
    unison_file = os.path.join(os.getenv("HOME"), ".unison", name)
    if os.path.isfile(unison_file):
        cmd = ["unison-gtk", name]
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT)
        proc.wait()
    else:
        print("Your config " + unison_file + " doesn't exist")


def main():
    remote_config = ""
    remote_target = ""

    local_ip = getIp()
    print("Local IP = %s" % str(local_ip))
    local_config = ipName[local_ip]
    print("Local config = %s" % str(local_config))
    # Remove _wifi to the name
    local_config = re.sub("_wifi", "", local_config)
    print("Local config after sub _wifi = %s" % str(local_config))

    if re.search("portable", local_config):
        remote_target = "server"
    elif re.search("server", local_config):
        remote_target = "portable"
        # Check if external disk is connected
        if os.path.isdir(extDisk):
            local_config = "external_disk"
            remote_config = "server"

    for remoteIp in ipName:
        if re.search(remote_target, ipName[remoteIp]):
            if checkAddress(remoteIp):
                remote_config = ipName[remoteIp]
                print("Remote IP = %s" % str(remoteIp))
                print("Remote config = %s" % str(remote_config))
                break

    if remote_config == "":
        MessageDialog(dialog_type='error', title="Automatic Synchronisation",
                      message1="Can't find Remote IP.\nLocal IP is " + str(local_ip) + ".").run()
    else:
        runSync(local_config, remote_config)


if __name__ == '__main__':
    main()
