#!/usr/bin/env python

# Written by Gregory Brancq
# June 2018
# Public domain software

"""
Program to specify automatically which unison configuration to use
Launch the synchronisation
"""
from datetime import datetime
import os
import re
import sys
import subprocess
import socket
from optparse import OptionParser

sys.path.append('../pythonCommon')
from message import MessageDialog

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
thunderbird_source = "/media/perso/data/thunderbird/*"
thunderbird_target = "/home/greg/Greg/work/config/thunderbird/Portable"
firefox_source = "/media/perso/data/firefox/*"
firefox_target = "/home/greg/Greg/work/config/firefox/Portable"

##############################################
#              Line Parsing
##############################################

parser = OptionParser()

parser.add_option(
    "--syncLocalData",
    action="store_true",
    dest="syncLocalData",
    default=False,
    help="Synchronize thunderbird and firefox data."
)

(parsedArgs, args) = parser.parse_args()

##############################################


def getIp():
    # print([(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET,
    # socket.SOCK_DGRAM)]][0][1]) ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def checkAddress(ad):
    """Check if address pings"""
    print("Check address " + ad)
    cmd = "ping -w 1 " + str(ad)
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()
    if proc.returncode == 0:
        return True
    return False


def rsyncData(src, dst):
    print("  " + src + " to " + dst)
    cmd = "rsync -rulpgvz --delete "
    cmd += src + " " + dst
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()
    if proc.returncode != 0:
        print("Error during rsync data")


# copy local data to config directory
def copyLocalData(local_config, remote_config):
    if (local_config == "portable") and (remote_config == "server"):
        print("Copy thunderbird data :")
        rsyncData(thunderbird_source, thunderbird_target)

        print("Copy firefox data :")
        rsyncData(firefox_source, firefox_target)


def runSync(local_config, remote_config):
    name = local_config + "-to-" + remote_config + "-mode_sata.prf"
    print("Run sync " + name)
    unison_file = os.path.join(os.getenv("HOME"), ".unison", name)
    if os.path.isfile(unison_file):
        cmd = "unison-gtk " + str(name)
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()
    else:
        print("Your config " + unison_file + " doesn't exist")


def main():
    remote_config = ""
    remote_target = ""

    local_ip = getIp()
    print "Local IP=" + str(local_ip)
    local_config = ipName[local_ip]
    print "Local config=" + str(local_config)
    # Remove _wifi to the name
    local_config = re.sub("_wifi", "", local_config)
    print "Local config 2=" + str(local_config)

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
                print "Remote IP=" + str(remoteIp)
                print "Remote config=" + str(remote_config)
                break

    if remote_config == "":
        MessageDialog(type_='error', title="Automatic Synchronisation",
                      message="Can't find Remote IP.\nLocal IP is " + str(local_ip) + ".").run()
    else:
        # if switch enabled or current day is sunday
        if parsedArgs.syncLocalData or (datetime.now().weekday() == 6):
            copyLocalData(local_config, remote_config)
        runSync(local_config, remote_config)


if __name__ == '__main__':
    main()
