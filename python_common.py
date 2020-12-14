#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Common functions
'''

import os
from os.path import expanduser
import sys
import re
import pwd
from datetime import datetime
import random

# use for graphical interface
try :
    import pygtk
    pygtk.require('2.0')
except ImportError as e:
    sys.exit("Issue with PyGTK.\n" + str(e))
try :
    import gtk
except (RuntimeError, ImportError) as e:
    sys.exit("Issue with GTK.\n" + str(e))



###############################################
###############################################
##                CLASS LOG                  ##
###############################################
###############################################

class LOGC(object):
    def __init__(self, file_name, prog_name, debug, gui=False):
        self.fileName = file_name
        self.progName = prog_name
        self.debug = debug
        self.gui = gui
        self.dtFormat = datetime.today().isoformat("_")

    def writeLog(self, msg):
        if self.debug :
            print " DBG : " + str(msg)
        
        msg += "\n"
        try :
            f = open(self.fileName, 'a+')
            f.write(msg)
            f.close()
        except IOError, OSError:
            pass

    def dbg(self, msg):
        mes = " [ debug ] " + self.dtFormat + " == " + msg
        if self.debug :
            print " DBG : " + self.progName + str(mes)
    def info(self, item, msg):
        mes = item + " [ info  ] " + self.dtFormat + " == " + msg
        self.writeLog(mes)
    def warn(self, item, msg):
        mes = item + " [warning] " + self.dtFormat + " == " + msg
        self.writeLog(mes)
    def error(self, item, msg):
        mes = item + " [ error ] " + self.dtFormat + " == " + msg
        self.writeLog(mes)
        print "  ERROR " + self.progName + " :   Code " + str(item) + "\n" + str(msg) + "\n"
    def exit(self, item, msg):
        self.debug = False
        if self.gui :
            mes = "ERROR " + self.progName + " :   Exit code " + str(item) + "\n" + str(msg) + "\n"
            MessageDialog(type_='error', title="ERROR " + self.progName + " code " + str(item), message=msg).run()
        else :
            mes = "  ERROR " + self.progName + " :   Exit code " + str(item) + "\n" + color_error + str(msg) + color_reset + "\n"
        self.writeLog(mes)
        sys.exit(color_error + mes + color_reset)





###############################################
## Message Dialog Class
###############################################

"""Shows a message. The message type, title and the message to be
displayed can be passed when initializing the class."""

class MessageDialog(object):
    """Shows a message. The message type, title and the message to be
    displayed can be passed when initializing the class."""

    def __init__(self, type_, title, message):
        self.type = type_
        if self.type == 'error':
            self.dialog = gtk.MessageDialog(
                    type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE)
        elif self.type == 'info':
            self.dialog = gtk.MessageDialog(
                    type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_CLOSE)
        elif self.type == 'question':
            self.dialog = gtk.MessageDialog(
                    type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
        elif self.type == 'entry':
            self.dialog = gtk.MessageDialog(
                    type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
            dialogBox = self.dialog.get_content_area()
            self.userEntry = gtk.Entry()
            self.userEntry.show()
            # the following will trigger OK response when enter is hit in the entry
            self.userEntry.connect( "activate", lambda w: self.dialog.response( gtk.RESPONSE_YES)) 
            dialogBox.pack_end(self.userEntry, False, False, 0)
        self.dialog.set_title(title)
        self.dialog.set_markup(message)
        self.dialog.show_all()

    def run(self):
        """Runs the dialog and closes it afterwards."""
        response = self.dialog.run()
        self.dialog.hide()
        if (response == gtk.RESPONSE_YES) and (self.type == 'entry') :
            return self.userEntry.get_text()
        else :
            return response


## End dialog
def MessageDialogEnd(warnC, errC, logFile, title, msg) :
    if (errC != 0) :
        msg += "\nError = " + str(errC)
        msg += "\nLog file = " + str(logFile)
        MessageDialog(type_='error', title=title, message=msg).run()
    else :
        if (warnC != 0) :
            msg += "\nWarning = " + str(warnC)
        msg += "\n\nLog file = " + str(logFile)
        MessageDialog(type_='info', title=title, message=msg).run()

###############################################






###############################################
###############################################
##             BASIC FUNCTIONS               ##
###############################################
###############################################

    
## Exit when receiving an exception
def sysKeybInt() :
    remove_lock_file()
    sys.exit(color_error + "\n#### Received Ctrl-C exception\n#### Quit properly" + color_reset)

## User login
def getUserLogin() :
    try :
        return os.environ['USER']
    except :
        print color_error + 'Cannot get the login user\n'
        sys.exit(-1)

def getHomeDir():
    return expanduser("~greg")

def getBinDir():
    return os.path.join(getHomeDir(),"Config/env/bin")

def getScriptDir():
    return os.path.join(getHomeDir(),"Config/env/scripts")

def getEnvDir():
    return os.path.join(getHomeDir(),"Config/env")

def getLogDir():
    return  os.path.join(getEnvDir(),"log")

## Get the human size of a file
def humanSize(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

## Verify lock file
def verify_lock_file(lockFile) :
    timeout = 0
    ## Verify that the lock file doesn't exist
    while os.path.isfile(lockFile) :
        if (timeout > 200) :
            remove_lock_file(lockFile)
            break
        else :
            import time
            time.sleep(1)
            timeout += 1

## Create lock file
def create_lock_file(lockFile) :
    ## Verify that the lock file doesn't exist
    verify_lock_file(lockFile)
    ## Create it.
    os.system('touch ' + lockFile)

## Delete lock file
def remove_lock_file(lockFile) :
    ## Remove lock file
    try :
        os.remove(lockFile)
    except :
        pass

## Random number
def getRandomSeed() :
    return random.randint(1,65536)

## Create a integer range
def parseRange(rangestr) :
    result = list()
    try :
        if (rangestr!="") :
            list0=rangestr.split(",")
            for list1 in list0 :
                list2=list1.split("-")
                if (len(list2)==2) : #range found
                    for i in range(int(list2[0]),int(list2[1])+1) :
                        result.append(i)
                else :
                  result.append(int(list2[0]))
    except :
        parser.error(" There is a problem with your parsed options")

    return(result)

## Determine if the file is executable.
def filetest_exe(file) :
    """Determine if the file is executable."""
    if not os.path.exists(file):
        return 0
    stat = os.path.stat
    statinfo = os.stat(file)
    mode = stat.S_IMODE(statinfo[stat.ST_MODE])
    if ((stat.S_IXUSR & mode) or (stat.S_IXGRP & mode) or (stat.S_IXOTH & mode)):
        return True
    return False
    
## Remove a directory
def remove_dir_file(path) :
    list_files = os.listdir(path)
    for file in list_files :
        try :
            os.remove(os.path.join(path, file))
        except OSError:
            pass

## Move files in another directory
def move_files(old_path, new_path) :
    list_files = os.listdir(old_path)
    for file in list_files :
        try :
            os.rename(os.path.join(old_path, file), os.path.join(new_path, file))
        except :
            pass


def sendMail(From, To, Cc, Subject, MessageText, MessageHtml):

    # Import smtplib for the actual sending function
    import smtplib
    # Import the email modules we'll need
    from cStringIO import StringIO
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.header import Header
    from email import Charset
    from email.generator import Generator

    # Default encoding mode set to Quoted Printable. Acts globally!
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
    # 'alternative’ MIME type – HTML and plain text bundled in one e-mail message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(Subject, 'utf-8')
    # Only descriptive part of recipient and sender shall be encoded, not the email address
    #msg['From'] = Header(From, 'utf-8')
    msg['From'] = From
    msg['To'] = To
    msg['Cc'] = Cc

    # Attach the parts with the given encodings.
    htmlpart = MIMEText(MessageHtml, 'html', 'UTF-8')
    msg.attach(htmlpart)
    textpart = MIMEText(MessageText, 'plain', 'UTF-8')
    msg.attach(textpart)

    # And here we have to instantiate a Generator object to convert the msg
    # object to a string (can't use msg.as_string, because that escapes
    # "From" lines).
    io = StringIO()
    g = Generator(io, False) # second argument means "should I mangle From?"
    g.flatten(msg)
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(From, [To], io.getvalue())
    s.quit()




###############################################
###############################################
##            ADVANCED FUNCTIONS             ##
###############################################
###############################################

def addFile(log, header, fileName, extAuth, typeList, warnNb) :
    log.info(header, "In  addFile fileName=" + str(fileName))
    dirN = os.path.dirname(fileName)
    dirN1=dirN.replace('(','\(')
    dirN2=dirN1.replace(')','\)')
    fileNameWoDir=re.sub(dirN2 + "\/", '', fileName)
    (fileN, extN) = os.path.splitext(fileNameWoDir)
    if extAuth.__contains__(extN) :
        log.info(header, "In  addFile dirN=" + str(dirN) + ", fileN=" + str(fileN) + ", extN=" + str(extN))
        typeList.append([dirN, fileN, extN])
        return (typeList, warnNb)
    else :
        warnNb += 1
        log.warn(header, "In  addFile file " + str(fileNameWoDir) + " is not a good extension as " + str(extAuth))
        return (typeList, warnNb)


def listFromArgs(log, header, args, ext) :
    log.info(header, "In  listFromArgs")
    typeList= list()
    warnNb = 0

    if (len(args) != 0) :
        for arg in args :
            #arg.encode('latin1')
            if (os.path.isdir(arg)) :
                dirName = arg
                log.info(header, "In  listFromArgs dir=" + str(arg))
                for dirpath, dirnames, filenames in os.walk(arg) :
                    for filename in filenames :
                        (typeList, warnNb) = addFile(log, header, os.path.join(dirpath, filename), ext, typeList, warnNb)

            elif (os.path.isfile(arg)) :
                log.info(header, "In  listFromArgs file=" + str(arg))
                (typeList, warnNb) = addFile(log, header, arg, ext, typeList, warnNb)

    log.info(header, "Out listFromArgs typeList=" + str(typeList))
    return (typeList, warnNb)




###############################################
###############################################
##                  COLOR                    ##
###############################################
###############################################

## Color definition
color            = dict()
color['red']     ='\033[31m'
color['green']   ='\033[32m'
color['blue']    ='\033[34m'
color['magenta'] ='\033[35m'
color['cyan']    ='\033[36m'
color['reset']   ='\033[39m\033[49m\033[0m'
color['blink']   ='\033[5m'
color['bold']    ='\033[1m'
color_default    = color['cyan']

color_info1 = color['cyan']
color_info2 = color['green']
color_cmd   = color['magenta']
color_warn  = color['blue']
color_error = color['red']
color_reset = color['reset']

