#!/usr/bin/env python
# -*-coding:Latin-1 -*

'''
Backup KMyMoney files
'''



## Import
import sys
import os, os.path
import re
from datetime import datetime
import filecmp
import shutil
from optparse import OptionParser

## common
from python_common import *
HEADER = "backupKMyMoney"

## directory
homeDir = getHomeDir()
logDir  = getLogDir()

###############################################



###############################################
###############################################
##              Line Parsing                 ##
###############################################
###############################################

parsedArgs = {}
parser = OptionParser()


parser.add_option(
    "-d",
    "--debug",
    action  = "store_true",
    dest    = "debug",
    default = False,
    help    = "Display all debug information"
    )

(parsedArgs , args) = parser.parse_args()

###############################################




###############################################
## Global variables
###############################################

t = str(datetime.today().isoformat("_"))
logFile = os.path.join(logDir, HEADER + "_" + t + ".log")
lockFile = os.path.join(logDir, HEADER + ".lock")

fileBackupList = []
fileBackupName = ""

fileName = "comptes.kmy"
fileBackupDir = "/home/greg/Backup/KMyMoney"
fileOriginal = os.path.join(homeDir, "Config/tools/kmymoney", fileName)

###############################################




###############################################
###############################################
##                FUNCTIONS                  ##
###############################################
###############################################

def findBackupFiles() :
    global log
    global fileBackupList
    log.info(HEADER, "In  findBackupFiles")
    fileBackupList = [ f for f in os.listdir(fileBackupDir) if (os.path.isfile(os.path.join(fileBackupDir,f))) ]
    log.info(HEADER, "Out findBackupFiles fileList=" + str(fileBackupList))


def backupToDo() :
    global log
    global fileBackupName
    log.info(HEADER, "In  backupToDo")

    # find the last backup file name
    findBackupFiles()

    ## Look if it's necessary to backup
    didBackup = False
    for f in fileBackupList :
        log.info(HEADER, "In  backupToDo fileBackup=" + str(f))
        comp = filecmp.cmp(fileOriginal, os.path.join(fileBackupDir, f))
        if comp :
            log.info(HEADER, "In  backupToDo fileBackup find")
            didBackup = True
            break

    if not didBackup :
        now = datetime.now()
        (fileN, extN) = os.path.splitext(fileName)
        newName = fileN + "_" + str(now.strftime("%Y-%m-%d") + extN)
        log.info(HEADER, "In  backupToDo copy newName=" + str(newName))
        shutil.copy2(fileOriginal, os.path.join(fileBackupDir, newName))

    log.info(HEADER, "Out backupToDo")

###############################################






###############################################
###############################################
###############################################
##                 MAIN                      ##
###############################################
###############################################
###############################################


def main() :
    global log
    log.info(HEADER, "In  main")

    ## Backup file
    backupToDo()
    
    log.info(HEADER, "Out main")



if __name__ == '__main__':
 
    ## Create log class
    log = LOGC(logFile, HEADER, parsedArgs.debug)

    main()

###############################################

