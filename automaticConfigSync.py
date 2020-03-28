#!/usr/bin/env python

# Written by Gregory Brancq
# June 2018
# Public domain software

"""
Program to check which unison configuration using and launch the synchronisation
"""
from datetime import datetime
import os
import re
import sys
import subprocess
import socket
from optparse import OptionParser

sys.path.append('/home/greg/Greg/work/env/pythonCommon')
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

##############################################
#              Line Parsing                 ##
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
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def checkAddress(ad):
    """Check if address pings"""
    print("Check address " + ad)
    runCmd = "ping -w 1 " + str(ad)
    procPopen = subprocess.Popen(runCmd, shell=True)
    procPopen.wait()
    if procPopen.returncode == 0:
        return True
    return False


def rsyncData(src, dst):
    print("  " + src + " to " + dst)
    cmd = "rsync -rulpgvz --delete "
    cmd += src + " " + dst
    procPopen = subprocess.Popen(cmd, shell=True)
    procPopen.wait()
    if procPopen.returncode != 0:
        print("Error during rsync data")


# copy local data to config directory
def copyLocalData(localCfg, remoteCfg):
    if (localCfg == "portable") and (remoteCfg == "server"):
        print("Copy thunderbird data :")
        rsyncData("/media/perso/data/thunderbird/*", "/home/greg/Greg/work/config/thunderbird/Portable")

        print("Copy firefox data :")
        rsyncData("/media/perso/data/firefox/*", "/home/greg/Greg/work/config/firefox/Portable")


def runSync(localCfg, remoteCfg):
    cfgName = localCfg + "-to-" + remoteCfg + "-mode_sata.prf"
    print("Run sync " + cfgName)
    unisonCfgFile = os.path.join(os.getenv("HOME"), ".unison", cfgName)
    if os.path.isfile(unisonCfgFile):
        runCmd = "unison-gtk " + str(cfgName)
        procPopen = subprocess.Popen(runCmd, shell=True)
        procPopen.wait()
    else:
        print("Your config " + unisonCfgFile + " doesn't exist")


def main():
    remoteCfg = ""
    remoteTarget = ""

    localIp = getIp()
    print "Local IP=" + str(localIp)
    localCfg = ipName[localIp]
    print "Local config=" + str(localCfg)
    # Remove _wifi to the name
    localCfg = re.sub("_wifi", "", localCfg)
    print "Local config 2=" + str(localCfg)

    if re.search("portable", localCfg):
        remoteTarget = "server"
    elif re.search("server", localCfg):
        remoteTarget = "portable"
        # Check if external disk is connected
        if os.path.isdir(extDisk):
            localCfg = "external_disk"
            remoteCfg = "server"

    for remoteIp in ipName:
        if re.search(remoteTarget, ipName[remoteIp]):
            if checkAddress(remoteIp):
                remoteCfg = ipName[remoteIp]
                print "Remote IP=" + str(remoteIp)
                print "Remote config=" + str(remoteCfg)
                break

    if remoteCfg == "":
        MessageDialog(type_='error', title="Automatic Synchronisation",
                      message="Can't find Remote IP.\nLocal IP is " + str(localIp) + ".").run()
    else:
        # if switch enabled or current day is sunday
        if (parsedArgs.syncLocalData) or (datetime.now().weekday() == 6):
            copyLocalData(localCfg, remoteCfg)
        runSync(localCfg, remoteCfg)


if __name__ == '__main__':
    main()
