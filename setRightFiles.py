#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Before, for each :
# > sudo chown -R greg:greg *
# Launch the program
# > setRightFiles --debug
# For each file
# > find . -type f -exec chmod 664 {} \;

import logging
import os.path
import shutil
import re
import sys
from optparse import OptionParser

sys.path.append('/home/greg/Config/env/pythonCommon')
from log import LogClass

##############################################
# Global variables
##############################################

progName = "setRightFiles"



##############################################
#              Line Parsing                  #
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
    "--dry-run",
    action="store_true",
    dest="dryrun",
    default=False,
    help="Display all debug information."
)

(parsed_args, args) = parser.parse_args()


##############################################


##############################################
#                 MAIN                       #
##############################################

def main():
    logger.info("START")

    for dirpath, dirnames, files in os.walk(".") :
        logger.info("dirpath = %s", dirpath)
        logger.info("dirnames = %s", dirnames)
        logger.info("files = %s", files)
        #for f in files :
        #    logger.info("File = %s", os.path.join(dirpath, f))

        # Cleaning .jpg and .nfo files
        for f in files :
            f_wpath = os.path.join(dirpath, f)
            if re.search(".jpg", f) or re.search(".png", f) or re.search(".nfo", f) :
                logger.info("find file to delete = %s", f_wpath)
                if not parsed_args.dryrun :
                    if os.path.isfile(f_wpath) :
                        os.remove(f_wpath) 
                        logger.info("delete f = %s", f_wpath)

        # Cleaning empty directory
        if not dirnames and not files :
            logger.info("find dir to delete = %s", dirpath)
            if not parsed_args.dryrun :
                os.rmdir(dirpath) 
                logger.info("delete dir = %s", dirpath)

        elif dirpath == "." :
            pass

        # Cleaning .actors dir
        elif re.search(".actors", dirpath) :
            logger.info("find .actors to delete = %s", dirpath)
            if not parsed_args.dryrun :
                for f in files :
                    os.remove(os.path.join(dirpath, f))
                os.rmdir(dirpath) 
                logger.info("delete %s", dirpath)

        # Compute
        else :
            dirpathTmp = dirpath + "_tmp"
            logger.info("find dir to compute = %s", dirpath)
            if not parsed_args.dryrun :
                # renommer dirpath en tmp
                logger.info("mv %s to %s" % (dirpath, dirpathTmp))
                os.rename(dirpath, dirpathTmp)
                # créer dirpath
                logger.info("create dir %s" % (dirpath))
                os.makedirs(dirpath)
                # mv tmp/* to dirpath
                logger.info("move files from %s to %s" % (dirpathTmp, dirpath))
                for f in files :
                    if os.path.isfile(os.path.join(dirpathTmp, f)) :
                        if not(re.search(".jpg", f)) or not(re.search(".nfo", f)) :
                            shutil.move(os.path.join(dirpathTmp, f), dirpath)
                logger.info("move dirs to %s" % (dirpath))
                for d in dirnames :
                    if os.path.isdir(os.path.join(dirpathTmp, d)) :
                        shutil.move(os.path.join(dirpathTmp, d), dirpath)
                # rm tmp
                logger.info("delete tmp dir %s" % (dirpathTmp))
                os.rmdir(dirpathTmp)


    logger.info("STOP\n")


if __name__ == '__main__':
    logger = LogClass(progName, parsed_args.debug).getLogger()
    main()

