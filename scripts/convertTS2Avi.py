#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Convert M2TS to AVI
'''



## Import
import sys
import os
import time, datetime
import subprocess
from optparse import OptionParser

## common
from python_common import *
HEADER = "M2tsTOAvi"

## directory
logDir   = getLogDir()

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

t = str(datetime.datetime.today().isoformat("_"))
logFile = os.path.join(logDir, HEADER + "_" + t + ".log")
errC = 0

###############################################





###############################################
###############################################
##                FUNCTIONS                  ##
###############################################
###############################################

def convertFile(fileList) :
    global log
    global errC
    log.info(HEADER, "In  convertFile")

    oldDir = os.getcwd()

    for (fileD, fileN, fileE) in fileList :
        log.info(HEADER, "In  convertFile directory " + str(fileD) + "  convertFile " + fileN + fileE)

        if (fileD != "") :
            os.chdir(fileD)

        cmd='ffmpeg -i "' + fileN + fileE + '" -threads 3 -r 29.97 -vcodec libxvid -s 1024x576 -aspect 16:9 -b 2000k -qmin 3 -qmax 5 -bufsize 4096 -mbd 2 -bf 2 -acodec libmp3lame -ar 48000 -ab 128k -ac 2 "' + fileN + '.avi"'
        log.info(HEADER, "In  convertFile cmd=" + str(cmd))
        procPopen = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT)
        procPopen.wait()
        if (procPopen.returncode != 0) :
            errC += 1
            log.error(HEADER, "In  convertFile file: issue with " + str(os.path.join(fileD, fileN + fileE)))

        if (fileD != "") :
            os.chdir(oldDir)

    log.info(HEADER, "Out convertFile")

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
    warnC = 0
    log.info(HEADER, "In  main")

    fileList = list()

    log.info(HEADER, "In  main parsedArgs=" + str(parsedArgs))
    log.info(HEADER, "In  main args=" + str(args))

    ## Create list of files
    extAuth=[".m2ts", ".M2TS"]
    (fileList, warnC) = listFromArgs(log, HEADER, args, extAuth)

    ## Verify if there is at least one video to convert
    if (len(fileList) == 0) :
        MessageDialog(type_='error', title="Convert M2TS files", message="\nNo video has been found\n").run()
    else :
        log.info(HEADER, "In  main videos to convert = " + str(len(fileList)))

    ## Convert them
    convertFile(fileList)

    ## End dialog
    MessageDialogEnd(warnC, errC, logFile, "Convert images", "\nJob fini : " + str(len(fileList)) + " video converties.")

    log.info(HEADER, "Out main")

###############################################




if __name__ == '__main__':
 
    ## Create log class
    log = LOGC(logFile, HEADER, parsedArgs.debug)

    main()


