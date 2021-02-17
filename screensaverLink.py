#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Screensaver Link

program to scan image files to determine different tags,
enable/disable whatever you want,
and create link for the screensaver.

"""


# use for graphical interface
import sys
try :
    import pygtk
    pygtk.require('2.0')
except ImportError as e:
    sys.exit("Issue with PyGTK.\n" + str(e))
try :
    import gtk
except (RuntimeError, ImportError) as e:
    sys.exit("Issue with GTK.\n" + str(e))
try :
    import gobject
except (RuntimeError, ImportError) as e:
    sys.exit("Issue with GOBJECT.\n" + str(e))

from gtk import RESPONSE_YES, RESPONSE_NO

# default system
import os, os.path
import re
import shutil
import copy
from optparse import OptionParser
from datetime import datetime

# tags for image
from PIL import Image
import warnings
# To avoid this kind of warnings
# /usr/lib/python2.7/dist-packages/PIL/Image.py:2514: DecompressionBombWarning: Image size (131208140 pixels) exceeds limit of 89478485 pixels, could be decompression bomb DOS attack.
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

# xml
import xml.etree.ElementTree as ET
from lxml import etree

sys.path.append('/home/greg/Config/env/pythonCommon')
from basic import getHomeDir, getToolsDir
from log import LogClass

###############################################
## Global variables
###############################################

progName = "screensaverLink"

# configuration files
progIcon = os.path.join(getToolsDir(), "icons", "screensaverLink.png")

## Official
imagesDir = os.path.join(getHomeDir(), "Images")
linkDir = os.path.join(getHomeDir(), ".screensaver")
configDir = os.path.join(getToolsDir(), progName)
configName = "config.xml"

## Test
#imagesDir = os.path.join(getToolsDir(), progName, "Test")
#linkDir = os.path.join(getHomeDir(), "Screensaver_test")
#configDir = os.path.join(getToolsDir(), progName)
#configName = "config_test.xml"

configN = os.path.join(configDir, configName)

# Minimum parameters for each image to be installed
minWidth  = 800
minHeight = 800


## Tag Columns
(
  COL_NAME,
  COL_ENABLE,
  COL_ENABLE_VISIBLE,
  COL_ENABLE_ACTIVATABLE
) = range(4)

COL_CHILDREN = 4

##############################################
#              Line Parsing                 ##
##############################################

parser = OptionParser()

parser.add_option(
    "-d",
    "--debug",
    action  = "store_true",
    dest    = "debug",
    default = False,
    help    = "Display all debug information"
    )

parser.add_option(
    "-c",
    "--create",
    action  = "store_true",
    dest    = "create",
    default = False,
    help    = "Read the tags and the config, then create the links in batch."
    )

(parsed_args, args) = parser.parse_args()

###############################################







###############################################
###############################################
##                  CLASS                    ##
###############################################
###############################################


class TagC() :

    def __init__(self) :
        self.tagDict = dict() # [tagName] = enable
        self.tagMultiList = list() # [tagname0, enable0], [tagname1, disable1], enable ]
        self.fileDict = dict() # [fileName] = tagList


    def __str__(self) :
        res = "\n"
        res += "#-----------------\n"
        res += "# Simple Tags\n"
        res += "#-----------------\n"
        tagsN = self.getSimpleTags()
        for tagN in tagsN :
            res += str(tagN) + " : " + str(self.tagDict[tagN]) + "\n"
        res += "\n\n"

        res += "#-----------------\n"
        res += "# Multiple Tags\n"
        res += "#-----------------\n"
        i = 1
        for tagsEnM in self.tagMultiList :
            res += "Tags " + str(i) + " enable=" + str(tagsEnM[1])  + "\n  "
            for tagEnM in tagsEnM[0] :
                res += str(tagEnM[0]) + " : " + str(tagEnM[1]) + ", "
            res += "\n"
            i += 1
        res += "\n\n"

        res += "#-----------------\n"
        res += "# Files\n"
        res += "#-----------------\n"
        fileNSort = self.getFiles()
        fileNSort.sort()
        for fileN in fileNSort :
            res += str(fileN) + " : "
            for tagN in self.fileDict[fileN] :
                res += str(tagN) + ", "
            res += "\n"
        res += "\n"

        return res


    def convertStrToBool(self, pattern) :
        # be sure string is a boolean
        if isinstance(pattern, str) :
            if pattern == 'True' :
                pattern = True
            else :
                pattern = False
        return pattern


    def getSimpleTags(self) :
        tagsNSort = self.tagDict.keys()
        tagsNSort.sort()
        return tagsNSort


    def getSimpleTagEn(self, tagN) :
        return self.tagDict[tagN]


    def setSimpleTagEn(self, tagN, tagEn) :
        self.tagDict[tagN.decode('utf-8')] = tagEn
        #logger.debug("Out setSimpleTagEn tagDict="+str(self.tagDict))


    def getFiles(self) :
        filesNSort = self.fileDict.keys()
        filesNSort.sort()
        return filesNSort


    def getFileTagsL(self, fileN) :
        tagsL = self.fileDict[fileN]
        tagsL.sort()
        return tagsL


    def addSimpleTag(self, tagN, tagEn) :
        logger.debug("In  addSimpleTag tagN="+str(tagN)+" tagEn="+str(tagEn))
        tagEn = self.convertStrToBool(tagEn)
        self.setSimpleTagEn(tagN, tagEn)
        logger.debug("Out addSimpleTag tagDict="+str(self.tagDict))


    def isAlreadyInMultiTag(self, tagMulti) :
        logger.debug("In  isAlreadyInMultiTag tagMulti="+str(tagMulti))
        found = False

        # Sort it
        tagMulti.sort()
        
        # Find
        for tagsEnM in self.tagMultiList :
            #logger.debug("In  isAlreadyInMultiTag tagsEnM="+str(tagsEnM))
            i = 0
            tagsM = tagsEnM[0]
            #logger.debug("In  isAlreadyInMultiTag tagsM="+str(tagsM))
            if tagsM.__len__() == tagMulti.__len__() :
                #logger.debug("In  isAlreadyInMultiTag same length tagsM="+str(tagsM))
                for tagM in tagsM :
                    #logger.debug("In  isAlreadyInMultiTag tagM="+str(tagM))
                    if tagM[0] == tagMulti[i][0] :
                        i += 1
                        #logger.debug("In  isAlreadyInMultiTag i="+str(i))
                    else :
                        i = 0
                        #logger.debug("In  isAlreadyInMultiTag i="+str(i))
                        break

            #logger.debug("In  isAlreadyInMultiTag i="+str(i))
            if (i == tagMulti.__len__()) :
                found = True
                break

        logger.debug("Out isAlreadyInMultiTag found=" + str(found))
        return found


    # With a tag name (included with + and -), 
    # it will return the element or None
    def findElt(self, tagName) :
        #logger.debug("In  findElt tagMultiList=" + str(self.tagMultiList))
        foundElt = None
        for tagsEnM in self.tagMultiList :
            #logger.debug("In  findElt tagsEnM=" + str(tagsEnM))
            newTagN = tagName
            for tagM in tagsEnM[0] :
                #logger.debug("In  findElt tagM=" + str(tagM))
                #logger.debug("In  findElt tagM[0]=" + str(tagM[0]))
                #logger.debug("In  findElt newTagN=" + str(newTagN))
                if re.search(tagM[0], newTagN) :
                    #logger.debug("In  findElt 1 newTagN=" + str(newTagN))
                    newTagN = re.sub(tagM[0], "", newTagN)
                    #logger.debug("In  findElt 2 newTagN=" + str(newTagN))
                else :
                    break
            #logger.debug("In  findElt 3 newTagN=" + str(newTagN))

            newTagN = re.sub("\+|\-| ", "", newTagN)
            if newTagN == "" :
                #logger.debug("In  findElt tagsEnM=" + str(tagsEnM))
                foundElt = tagsEnM
                break
        
        logger.debug("In  findElt tagsEnM=" + str(tagsEnM))
        return foundElt


    # With a tag name (included with + and -), 
    # it will set enable/disable value
    def setEnOnMulti(self, tagName, tagEn) :
        logger.debug("In  setEnOnMulti tagName=" + str(tagName) + ", tagEn=" + str(tagEn))
        foundElt = self.findElt(tagName)
        if foundElt is not None :
            self.tagMultiList.remove(foundElt)
            self.addMultiTag(foundElt[0], tagEn)


    def addMultiTag(self, tagL, tagEn) :
        logger.debug("In  addMultiTag tagL="+str(tagL)+", tagEn="+str(tagEn))
        # be sure tagEn is a boolean
        tagEn = self.convertStrToBool(tagEn)

        # Decode name
        newTagL = list()
        for tag in tagL :
            #logger.debug("In  addMultiTag tag="+str(tag))
            tag[1] = self.convertStrToBool(tag[1])
            newTagL.append([tag[0].decode('utf-8'), tag[1]])
        #logger.debug("In  addMultiTag newTagL="+str(newTagL))

        # Already exists ?
        if not self.isAlreadyInMultiTag(newTagL) :
            #logger.debug("In  addMultiTag tagEn="+str(tagEn))
            self.tagMultiList.append([newTagL, tagEn])
            self.tagMultiList.sort()


    def addFileAndTags(self, fileN, tagN) :
        logger.debug("In  addFileAndTags fileN="+str(fileN)+ " tagN="+str(tagN))
        fileNDec = fileN.decode('utf-8')
        tagNDec = tagN.decode('utf-8')
        if not self.fileDict.has_key(fileNDec) :
            tagList = list()
            tagList.append(tagNDec)
            self.fileDict[fileNDec] = tagList
        else :
            tagList = self.fileDict[fileNDec]
            if not tagList.__contains__(tagNDec) :
                tagList.append(tagNDec)


    # Return tags with a two-level ordered
    def getSimpleTagsByHier(self) :
        resDict = dict()
        for tagN in self.getSimpleTags() :
            (lvl1, lvl2) = re.split("/", tagN)
            tagEn = self.getSimpleTagEn(tagN)
            if not resDict.has_key(lvl1) :
                #logger.debug("In  getSimpleTagsByHier add lvl1="+str(lvl1)+" lvl2="+str(lvl2)+" tagEn="+str(tagEn))
                l = list()
                l.append([lvl2, tagEn])
                resDict[lvl1] = [[lvl2, tagEn]]
                #logger.debug("In  getSimpleTagsByHier resDict="+str(resDict))
            else :
                tagsList = resDict[lvl1]
                find = False

                #logger.debug("In  getSimpleTagsByHier tagsList="+str(tagsList))
                for tagLvl2 in tagsList :
                    #logger.debug("In  getSimpleTagsByHier tagLvl2="+str(tagLvl2))
                    if tagLvl2[0] == lvl2 :
                        find = True
                        break

                if not find :
                    tagsList.append([lvl2, tagEn])

        logger.debug("In  getSimpleTagsByHier res="+str(resDict))
        return resDict


    ## read tools configuration file
    def readConfig(self) :
        logger.info("In  readConfig " + configN)

        if not os.path.isfile(configN) :
            logger.info("In  readConfig config file doesn't exist.")
            self.writeConfig()

        else :
            # Initialize variables
            self.tagDict = dict()
            self.tagMultiList = list()

            # Open config file
            tree = ET.parse(configN).getroot()

            # Simple Tags part
            for simpleTagTree in tree.iter("simpleTag") :
                tagName = None
                tagEnable = None

                # Get tag name
                if "name" in simpleTagTree.attrib :
                    tagName = simpleTagTree.attrib["name"]
                # Get tag enable
                if "enable" in simpleTagTree.attrib :
                    tagEnable = simpleTagTree.attrib["enable"]
                
                self.addSimpleTag(tagName, tagEnable)

            # Multiple Tags part
            for multiTagsTree in tree.iter("multiTags") :
                tagsEnable = None

                # Get tag enable
                if "enable" in multiTagsTree.attrib :
                    tagsEnable = multiTagsTree.attrib["enable"]

                # Find multi tag
                tagsL = list()
                for multiTagTree in multiTagsTree.iter("multiTag") :
                    tagName = None
                    tagEnable = None

                    # Get tag name
                    if "name" in multiTagTree.attrib :
                        tagName = multiTagTree.attrib["name"]
                    # Get tag enable
                    if "enable" in multiTagTree.attrib :
                        tagEnable = multiTagTree.attrib["enable"]
                    tagsL.append([tagName, tagEnable])
                
                self.addMultiTag(tagsL, tagsEnable)

            # Files part
            for fileTree in tree.iter("file") :
                fileName = None
                # Get file name
                if "name" in fileTree.attrib :
                    fileName = fileTree.attrib["name"]
                # Find file tags
                for tagTree in fileTree.iter("fileTag") :
                    tagName = tagTree.text
                    self.addFileAndTags(fileName, tagName)

        logger.info("Out readConfig")


    ## write tools configuration file
    def writeConfig(self) :
        logger.info("In  writeConfig " + configN)
        
        tagsAndFilesTree = etree.Element("TagsFiles")
        tagsAndFilesTree.addprevious(etree.Comment("!!! Don't modify this file !!!"))
        tagsAndFilesTree.addprevious(etree.Comment("Managed by " + progName))

        # Simple Tags part
        simpleTagsTree = etree.SubElement(tagsAndFilesTree, "simpleTags")
        tagsN = self.getSimpleTags()
        #logger.debug("In  writeConfig tagsN="+str(tagsN))
        for tagN in tagsN :
            # Create the element tree
            #logger.debug("In  writeConfig tagN="+str(tagN)+" enable="+str(self.getSimpleTagEn(tagN)))
            tagTree = etree.SubElement(simpleTagsTree, "simpleTag")
            tagTree.set("name", tagN)
            tagTree.set("enable", str(self.getSimpleTagEn(tagN)))
          
        # Multiple Tags part
        multiTagsTree = etree.SubElement(tagsAndFilesTree, "multiTagsTree")
        for tagsEnM in self.tagMultiList :
            #logger.debug("In  writeConfig multiTag="+str(tagsEnM[0])+" enable="+str(tagsEnM[1]))
            # Create the element tree
            multiTagsT = etree.SubElement(multiTagsTree, "multiTags")
            multiTagsT.set("enable", str(tagsEnM[1]))
            for tagM in tagsEnM[0] :
                #logger.debug("In  writeConfig tagN="+str(tagM[0])+" enable="+str(tagM[1]))
                multiTagT = etree.SubElement(multiTagsT, "multiTag")
                multiTagT.set("name", tagM[0])
                multiTagT.set("enable", str(tagM[1]))

        # Files part
        filesTree = etree.SubElement(tagsAndFilesTree, "files")
        filesN = self.getFiles()
        for fileN in filesN :
            # Create the element tree
            #logger.debug("In  writeConfig fileN="+str(fileN)+" tagsList="+str(self.getFileTagsL(fileN)))
            tagsFTree = etree.SubElement(filesTree, "file")
            tagsFTree.set("name", fileN)
            for tag in self.getFileTagsL(fileN) :
                etree.SubElement(tagsFTree, "fileTag").text = tag
 
        # Save to XML file
        doc = etree.ElementTree(tagsAndFilesTree)
        doc.write(configN, encoding='utf-8', method="xml", pretty_print=True, xml_declaration=True) 
            
        logger.info("Out writeConfig " + configN)


    def readTag(self, fileN) :
        logger.info("In  readTag file=" + str(fileN))
        im = Image.open(fileN)
        attr = True
        try :
            imL = im.applist
        except :
            logger.warning("In  readTag file="+str(fileN)+" has no tags")
            attr = False
        
        good = True
        (width, height) = im.size
        if (width < minWidth) or (height < minHeight) :
            logger.warning("In  readTag size of file="+str(fileN)+" is too small (width = " + str(width) + ", height = " + str(height)+ ").")
            good = False

        if attr and good :
            for segment, content in imL :
                try :
                    marker, body = content.split('\x00', 1)
                    if segment == 'APP1' and marker == 'http://ns.adobe.com/xap/1.0/' :
                        root = ET.fromstring(body)

                        for levelRDF in root :
                            #print "LevelRDF=" + levelRDF.tag
                            for levelDescription in levelRDF :
                                #print "levelDescription.tag=" + levelDescription.tag
                                for levelTagsList in levelDescription :
                                    #print "levelTagsList.tag=" + levelTagsList.tag
                                    if levelTagsList.tag == "{http://www.digikam.org/ns/1.0/}TagsList" :
                                        for levelSeq in levelTagsList :
                                            #print "levelSeq.tag=" + levelSeq.tag
                                            for levelLi in levelSeq :
                                                tagN = levelLi.text
                                                if not self.tagDict.has_key(tagN) :
                                                    self.addSimpleTag(tagN, "True")
                                                self.addFileAndTags(fileN, tagN)
                except ValueError as errValueError :
                    logger.warning("In  readTag ValueError fileN"+str(fileN)+"\n  error="+str(errValueError))
                except ET.ParseError as errParseError :
                    logger.warning("In  readTag ParseError fileN"+str(fileN)+"\n  error="+str(errParseError))


    def scanTags(self) :
        logger.info("In  scanTags")

        # Keep simple tag config backup
        oldTagDict = copy.deepcopy(self.tagDict)

        # Initialize
        self.tagDict = dict()
        self.fileDict = dict()

        # For all images
        if os.path.isdir(imagesDir) :
            for dirpath, dirnames, filenames in os.walk(imagesDir) :  # @UnusedVariable
                logger.debug("In  scanTags dirpath="+str(dirpath)+" dirnames="+str(dirnames)+" filenames="+str(filenames))
                if ( not(re.search(".dtrash", dirpath)) and (filenames.__len__ != 0) ) :
                    for filename in filenames :
                        extAuth=[".jpg", ".JPG", ".jpeg", ".JPEG", ".tif", ".TIF", ".gif", ".GIF", ".bmp", ".BMP"]
                        (fileN, extN) = os.path.splitext(filename)
                        if extAuth.__contains__(extN) :
                            fileWithPath = os.path.join(dirpath, filename)
                            self.readTag(fileWithPath)

        # Set the precedent config for simple tags
        for oldTagN in oldTagDict.keys() :
            if self.tagDict.has_key(oldTagN) :
                self.setSimpleTagEn(oldTagN, oldTagDict[oldTagN])
            
        # Check if tag exists for all multi tags
        #removeIt = False
        #for tagsEnM in self.tagMultiList :
        #    newTagsEnM = list()
        #    removeIt = list()
        #    for tagEnM in tagsEnM[0] :
        #        if not removeIt :
        #            for tagEnM in removeIt :
        #                self.tagMultiList[tagsEnM].remove[
        #        if not self.tagDict.has_key(tagEnM[0]) :
        #            removeIt.append([tagEnM[0], tagEnM[1]])

        #    if removeIt :
        #        self.tagMultiList.remove(tagsEnM)

        logger.info("Out scanTags")


    def copyTags(self, tagsToCopy) :
        logger.info("In  copyTags tagsToCopy=" + str(tagsToCopy))
        
        # Create link
        tagMulti = list()
        for sel in tagsToCopy :
            tagMulti.append([sel[0] + "/" + sel[1], sel[2]])
        logger.debug("In  copyTags tagMulti="+str(tagMulti))

        # Add it
        self.addMultiTag(tagMulti, True)

        logger.info("Out copyTags")


    # With a tag name (included with + and -), 
    def delTags(self, tagsToDelete) :
        logger.info("In  delTags tagsToDelete=" + str(tagsToDelete))
        for sel in tagsToDelete :
            foundElt = self.findElt(sel[0])
            if foundElt is not None :
                self.tagMultiList.remove(foundElt)
        logger.info("Out delTags")


    def createLinks(self) :
        logger.info("In  createLinks")
        # delete link directory
        if os.path.isdir(linkDir) :
            shutil.rmtree(linkDir)
        os.makedirs(linkDir)

        i=0
        for fileN in self.getFiles() :
            logger.debug("In  createLinks fileN="+str(fileN))
            tagsList = self.getFileTagsL(fileN)
            logger.debug("In  createLinks tagsList="+str(tagsList))

            # filter with simple tags
            installSimple = False
            for tagN in tagsList :
                if self.tagDict.has_key(tagN) :
                    logger.debug("In  createLinks tagN="+str(tagN)+"  en="+str(self.tagDict[tagN]))
                    if self.tagDict[tagN] :
                        logger.debug("In  createLinks installSimple tagN="+str(tagN)+"  en="+str(self.tagDict[tagN]))
                        installSimple = True
                    else :
                        installSimple = False
                        break
                else :
                    logger.debug("In  createLinks tagN="+str(tagN)+" doesn't exist in tagDict")

            # filter with multiple tags
            matchFound = False
            installMulti = None
            logger.debug("In  createLinks tagMultiList="+str(self.tagMultiList))
            for tagsEnM in self.tagMultiList :
                matchFoundOnce = False
                logger.debug("In  createLinks tagsEnM="+str(tagsEnM))
                if tagsEnM[1] :
                    for tagM in tagsEnM[0] :
                        logger.debug("In  createLinks tagM="+str(tagM))
                        # for enable, each tag must be present
                        if tagsList.__contains__(tagM[0]) :
                            logger.debug("In  createLinks 1")
                            matchFoundOnce = True
                            if tagM[1] :
                                logger.debug("In  createLinks 2")
                                if installMulti is None :
                                    installMulti = True
                            else :
                                logger.debug("In  createLinks 3")
                                installMulti = False
                        else :
                            logger.debug("In  createLinks 4")
                            matchFoundOnce = False
                            break

                if matchFoundOnce :
                    matchFound = True

            logger.debug("In  createLinks matchFound="+str(matchFound))
            logger.debug("In  createLinks installMulti="+str(installMulti))
            logger.debug("In  createLinks installSimple="+str(installSimple))

            # installation priority
            install = False
            if matchFound :
                if installMulti :
                    install = True
            elif installSimple :
                install = True

            # installation
            logger.debug("In  createLinks install="+str(install))
            if install :
                curDir = os.getcwd()
                os.chdir(linkDir)

                # create link name
                linkN = re.sub(getHomeDir(), "", fileN)
                linkN = re.sub("/", "_", linkN)
                linkN = re.sub("^_", "", linkN)
                os.symlink(fileN, linkN)
                logger.info("In  createLinks file="+str(fileN)+", link="+str(linkN))
                i += 1
        
                os.chdir(curDir)

        logger.info("Out createLinks " + str(i) + " images ont été ajoutés.")
        return i

###############################################







###############################################
###############################################
##                  CLASS                    ##
###############################################
###############################################

class GuiC(gtk.Window) :

    def __init__(self) :
        self.simpleGuiC = TagGuiC(self, False)
        self.multiGuiC = TagGuiC(self, True)


    def run(self):
        logger.info("In  run")

        # create the main window
        self.createWin()
        
        # display it
        gtk.main()

        logger.info("Out run")


    def on_destroy(self, widget):
        gtk.main_quit()
        

    def createWin(self):
        logger.info("In  createWin")

        #
        # Main window
        #

        gtk.Window.__init__(self)
        try :
            self.set_icon_from_file(progIcon)
        except gobject.GError as err :
            logger.warning("In  createWin progIcon="+str(progIcon)+"\n  error="+str(err))
        self.connect("destroy", self.on_destroy)

        self.set_title("Screensaver Images Tags")
        self.set_border_width(5)
        width = 1000
        height = 600
        self.set_size_request(width, height)


        #
        # Vertical box = tag lists + buttons
        #
        vTagBut = gtk.VBox(False, 5)
        #vTagBut.set_border_width(5)
        self.add(vTagBut)


        # Tag lists
        #

        # Horizontal box = tag list simple + buttons + multiple
        #
        hSimpleButMultiple = gtk.HBox(False, 5)
        hSimpleButMultiple.set_border_width(5)


        # Simple list
        #
        # Create the scrolled windows
        simpleTagSW = gtk.ScrolledWindow()
        simpleTagSW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        simpleTagSW.set_shadow_type(gtk.SHADOW_IN)
        simpleTagSW.set_size_request(300, height-100)
        # Create tags treeview
        simpleTagSW.add(self.simpleGuiC.createTagTv())

        hSimpleButMultiple.pack_start(simpleTagSW, False, False)


        # Create buttons
        #
        tagButTab = gtk.Table(2, 1, False)
        #tagButTab.set_row_spacings(5)
        #tagButTab.set_col_spacings(5)

        # copy multiple selection
        gtk.stock_add([(gtk.STOCK_GO_FORWARD, "", 0, 0, "")])
        self.copyBut = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.copyBut.connect("clicked", self.onCopy)
        self.copyBut.set_sensitive(False)
        tagButTab.attach(self.copyBut, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND, 10, 10)
        # remove multiple selection
        gtk.stock_add([(gtk.STOCK_GO_BACK, "", 0, 0, "")])
        self.delBut = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.delBut.connect("clicked", self.onDelete)
        self.delBut.set_sensitive(False)
        tagButTab.attach(self.delBut, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND, 10, 10)

        hSimpleButMultiple.pack_start(tagButTab, False, False)


        # Multiple list
        #
        # Create the scrolled windows
        multiTagSW = gtk.ScrolledWindow()
        multiTagSW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        multiTagSW.set_shadow_type(gtk.SHADOW_IN)
        #multiTagSW.set_size_request(width*3/5, height)
        # Create tags treeview
        # trick to copy 
        self.multiGuiC.tagC.tagMultiList = self.simpleGuiC.tagC.tagMultiList
        multiTagSW.add(self.multiGuiC.createTagTv())

        hSimpleButMultiple.pack_start(multiTagSW, True, True)

        vTagBut.add(hSimpleButMultiple)



        # Buttons
        #

        # Create buttons
        butTab = gtk.Table(1, 5, True)

        # scan tags
        gtk.stock_add([(gtk.STOCK_REFRESH, "Lire les tags", 0, 0, "")])
        scanBut = gtk.Button(stock=gtk.STOCK_REFRESH)
        scanBut.connect("clicked", self.onScan)
        butTab.attach(scanBut, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND, 0, 0)
        # create links
        gtk.stock_add([(gtk.STOCK_EXECUTE, "Créé les images", 0, 0, "")])
        exeBut = gtk.Button(stock=gtk.STOCK_EXECUTE)
        exeBut.connect("clicked", self.onExecute)
        butTab.attach(exeBut, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND, 0, 0)
        # quit
        quitBut = gtk.Button(stock=gtk.STOCK_QUIT)
        quitBut.connect("clicked", self.on_destroy)
        butTab.attach(quitBut, 4, 5, 0, 1, gtk.EXPAND, gtk.EXPAND, 0, 0)

        vTagBut.pack_start(butTab, False, False, 10)

        # Display the window
        self.show_all()

        logger.info("Out createWin")


    def onCopy(self, button=None) :
        self.simpleGuiC.onCopyTags()
        # copy data
        self.multiGuiC.tagC.tagMultiList = self.simpleGuiC.tagC.tagMultiList
        #self.simpleGuiC.createModel()
        self.multiGuiC.createModel()


    def onDelete(self, button=None) :
        self.multiGuiC.onDelTags()


    def onScan(self, button=None) :
        self.simpleGuiC.onScanTags()


    def onExecute(self, button=None) :
        # copy data
        self.simpleGuiC.tagC.tagMultiList = self.multiGuiC.tagC.tagMultiList
        self.simpleGuiC.onExeTags()







class TagGuiC(gtk.Window) :

    def __init__(self, parentW, multi) :
        # window parameter
        self.mainWindow = parentW
        self.treeview = None

        self.tagC = TagC()
        self.model = self.initModel()
        self.multi = multi  # false = tag list left (single)
                            # true  = tag list right (multiple)

        self.memColEn = "current"
        self.memColEnMulti = "current"
        self.selMulti = list()  # [lvl1, lvl2, enable] (single)
                                # [tagName, tagEnable] (multiple)

        if not self.multi :
            self.tagC.readConfig()
            logger.info("TagC = \n" + str(self.tagC))


    def initModel(self) :
        # create tree store
        return gtk.TreeStore(
                    gobject.TYPE_STRING,
                    gobject.TYPE_BOOLEAN,
                    gobject.TYPE_BOOLEAN,
                    gobject.TYPE_BOOLEAN)


    def createTagTv(self) :
        logger.debug("In  createTagTv")

        # create model
        self.createModel()

        # create tag treeview
        self.treeview = gtk.TreeView(self.model)
        self.treeview.set_rules_hint(True)
        self.treeview = self.addCol(self.treeview)
        self.treeview.expand_all()

        treeselect = self.treeview.get_selection()
        treeselect.set_mode(gtk.SELECTION_MULTIPLE)
        treeselect.connect('changed', self.onChanged)

        logger.debug("Out createTagTv")
        return self.treeview


    # Convert tag multi list to a special name (included with + and -)
    def convertListToSpecialName(self, listToConvert) :
        res = str()
        for pattern in listToConvert :
            if pattern[1] :
                res += "+ "
            else :
                res += "- "
            res += pattern[0] + " "
        res = re.sub(" $", "", res)
        return res


    def createModel(self) :
        logger.info("In  createModel multi=" + str(self.multi))
        topLvl = list()
        self.model.clear()

        ## For multiple tags
        if self.multi :
            for tagsEnM in self.tagC.tagMultiList :
                tagLinfo = list()

                tagsName = self.convertListToSpecialName(tagsEnM[0])
                tagEn = tagsEnM[1]

                # name
                tagLinfo.append(tagsName)
                # enable
                tagLinfo.append(tagEn)
                # visible
                tagLinfo.append(True)
                # activatable
                tagLinfo.append(True)

                topLvl.append(tagLinfo)


        ## For simple tags
        else :
            # Construct list to put in model 
            tagsDict = self.tagC.getSimpleTagsByHier()
            tagsDictSort = tagsDict.keys()
            tagsDictSort.sort()
            for tag in tagsDictSort :
                #logger.debug("In  createModel lvl1="+str(tag))

                ## Level 2
                lvl2L = list()
                for lvl2 in tagsDict[tag] :
                    #logger.debug("In  createModel lvl2="+str(lvl2))
                    lvl2info = list()

                    # name
                    lvl2info.append(lvl2[0])
                    # enable
                    lvl2info.append(lvl2[1])
                    # visible
                    lvl2info.append(True)
                    # activatable
                    lvl2info.append(True)
                    #logger.debug("In  createModel lvl2info="+str(lvl2info))

                    lvl2L.append(lvl2info)

                ## Level 1
                lvl1L = list()
                # name
                lvl1L.append(tag)
                # enable
                lvl1L.append(False)
                # visible
                lvl1L.append(False)
                # activatable
                lvl1L.append(False)
                #logger.debug("In  createModel lvl1L="+str(lvl1L))

                # Add level 2
                lvl1L.append(lvl2L)

                topLvl.append(lvl1L)


        ## Add data to the tree store
        logger.debug("In  createModel topLvl="+str(topLvl))
        if topLvl :
            for tag in topLvl :
                tagIter = self.model.append(None)

                self.model.set(tagIter,
                    COL_NAME, tag[COL_NAME],
                    COL_ENABLE, tag[COL_ENABLE],
                    COL_ENABLE_VISIBLE, tag[COL_ENABLE_VISIBLE],
                    COL_ENABLE_ACTIVATABLE, tag[COL_ENABLE_ACTIVATABLE]
                )

                if not self.multi :
                    for lvl2 in tag[COL_CHILDREN] :
                        versionIter = self.model.append(tagIter)
                        self.model.set(versionIter,
                            COL_NAME, lvl2[COL_NAME],
                            COL_ENABLE, lvl2[COL_ENABLE],
                            COL_ENABLE_VISIBLE, lvl2[COL_ENABLE_VISIBLE],
                            COL_ENABLE_ACTIVATABLE, lvl2[COL_ENABLE_ACTIVATABLE]
                        )

        if self.treeview is not None :
            self.treeview.expand_all()

        logger.info("Out createModel")


    def addCol(self, treeview) :
        logger.debug("In  addCol")
        model = treeview.get_model()

        # Column for tag's enable
        renderer = gtk.CellRendererToggle()
        renderer.set_property("xalign", 0.0)
        renderer.connect("toggled", self.onToggledItem, model)
        column = gtk.TreeViewColumn("Sélection", renderer, active=COL_ENABLE,
                                    visible=COL_ENABLE_VISIBLE, activatable=COL_ENABLE_ACTIVATABLE)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_clickable(True)
        column.set_fixed_width(80)
        column.connect("clicked", self.onColEnable, model)

        treeview.append_column(column)

        # Column for tag's name
        renderer = gtk.CellRendererText()
        renderer.set_property("xalign", 0.0)
        column = gtk.TreeViewColumn("Nom des tags", renderer, text=COL_NAME)
        column.set_clickable(False)

        treeview.append_column(column)
        logger.debug("Out addCol")
        return treeview


    # When the user clicks on the column "enable"
    def onColEnable(self, cell, model) :
        if self.multi :
            logger.info("In  onColEnable memColEnMulti=" + str(self.memColEnMulti))

            if self.memColEnMulti == "all" :
                self.memColEnMulti = "none"
            elif self.memColEnMulti == "none" :
                self.memColEnMulti = "current"
            elif self.memColEnMulti == "current" :
                self.memColEnMulti = "all"

            if self.memColEnMulti == "current" :
                self.tagC.readConfig()
            else :
                for tagsEnM in self.tagC.tagMultiList :
                    tagsName = self.convertListToSpecialName(tagsEnM[0])
                    if self.memColEnMulti == "all" :
                        self.tagC.setEnOnMulti(tagsName, True)
                    elif self.memColEnMulti == "none" :
                        self.tagC.setEnOnMulti(tagsName, False)

        else :
            logger.info("In  onColEnable memColEn=" + str(self.memColEn))

            if self.memColEn == "all" :
                self.memColEn = "none"
            elif self.memColEn == "none" :
                self.memColEn = "current"
            elif self.memColEn == "current" :
                self.memColEn = "all"

            if self.memColEn == "current" :
                self.tagC.readConfig()
            else :
                for tagN in self.tagC.getSimpleTags() :
                    if self.memColEn == "all" :
                        self.tagC.setSimpleTagEn(tagN, True)
                    elif self.memColEn == "none" :
                        self.tagC.setSimpleTagEn(tagN, False)

        # update model
        self.createModel()

        logger.info("Out onColEnable")


    # each time selection changes, this function is called
    def onChanged(self, selection) :
        logger.info("In  onChanged")
        model, rows = selection.get_selected_rows()

        self.selMulti = list()
        for row in rows :
            iterSel = model.get_iter(row)
            
            if self.multi :
                selName = model.get_value(iterSel, COL_NAME)
                selEn = model.get_value(iterSel, COL_ENABLE)
                self.selMulti.append([selName.decode('utf-8'), selEn])

                if self.selMulti.__len__() > 0 :
                    self.mainWindow.delBut.set_sensitive(True)
                else :
                    self.mainWindow.delBut.set_sensitive(False)

            else :
                iterSel_has_child = model.iter_has_child(iterSel)

                if iterSel_has_child :
                    selLvl1 = model.get_value(iterSel, COL_NAME)
                    selLvl2 = None
                    selEn = False
                elif not iterSel_has_child :
                    iterSelParent = model.iter_parent(iterSel)
                    selLvl1 = model.get_value(iterSelParent, COL_NAME)
                    selLvl2 = model.get_value(iterSel, COL_NAME)
                    selEn = model.get_value(iterSel, COL_ENABLE)
                    self.selMulti.append([selLvl1.decode('utf-8'), selLvl2.decode('utf-8'), selEn])
        
                if self.selMulti.__len__() > 1 :
                    self.mainWindow.copyBut.set_sensitive(True)
                else :
                    self.mainWindow.copyBut.set_sensitive(False)

        logger.info("Out onChanged selMulti=" + str(self.selMulti))


    # When user clicks on a box
    def onToggledItem(self, cell, path_str, model) :
        logger.info("In  onToggledItem")

        iterSel = model.get_iter_from_string(path_str)
        
        if self.multi :
            # Get name
            selName = model.get_value(iterSel, COL_NAME)
            # Get enable (before click)
            selEnable = model.get_value(iterSel, COL_ENABLE)

            logger.debug("selName=" + str(selName))
            logger.debug("selEnable=" + str(selEnable))

            # Disable
            # From True to False (as value is before clicking)
            if selEnable :
                self.tagC.setEnOnMulti(selName.decode('utf-8'), False)
                model.set(iterSel, COL_ENABLE, False)

            # Enable
            # From False to True
            else :
                self.tagC.setEnOnMulti(selName.decode('utf-8'), True)
                model.set(iterSel, COL_ENABLE, True)

        else :
            # Get enable (before click)
            selEnable = model.get_value(iterSel, COL_ENABLE)
            # Get lvl2 name
            selLvl2 = model.get_value(iterSel, COL_NAME)
            # Get lvl1 name
            iterSelParent = model.iter_parent(iterSel)
            selLvl1 = model.get_value(iterSelParent, COL_NAME)
            # Set tag name
            selTagN = selLvl1 + "/" + selLvl2

            logger.debug("selLvl1=" + str(selLvl1))
            logger.debug("selLvl2=" + str(selLvl2))
            logger.debug("selEnable=" + str(selEnable))

            # Disable
            # From True to False (as value is before clicking)
            if selEnable :
                self.tagC.setSimpleTagEn(selTagN.decode('utf-8'), False)
                model.set(iterSel, COL_ENABLE, False)

            # Enable
            # From False to True
            else :
                self.tagC.setSimpleTagEn(selTagN.decode('utf-8'), True)
                model.set(iterSel, COL_ENABLE, True)

        logger.info("Out onToggledItem")


    # Create multiple tags
    def onCopyTags(self) :
        self.tagC.copyTags(self.selMulti)


    # Delete multiple tags
    def onDelTags(self) :
        self.tagC.delTags(self.selMulti)
        self.createModel()


    # Create multiple tags
    def onScanTags(self) :
        self.tagC.scanTags()
        self.createModel()


    # Create links
    def onExeTags(self) :
        self.tagC.writeConfig()
        nb = self.tagC.createLinks()
        MessageDialog(type_='info', title="ScreenSaver Link", message=str(nb) + " images ont été ajoutés.").run()


###############################################







###############################################
###############################################
###############################################
##                 MAIN                      ##
###############################################
###############################################
###############################################


def main() :
    ## Graphic interface
    if parsed_args.create :
        tagC = TagC()
        tagC.scanTags()
        tagC.readConfig()
        nb = tagC.createLinks()
    else :
        gui = GuiC()
        gui.run()


if __name__ == '__main__':
    logger = LogClass(progName, parsed_args.debug).getLogger()
    main()

###############################################

