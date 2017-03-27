#!/bin/bash -f

# Program to backup Android phone directory

# Detect phone
# Mount phone
# Sync directories
# Umount phone

progName=$(basename "$0")

# Log file
logF="$HOME/Greg/work/env/log/${progName}_`date +%Y-%m-%d_%H:%M:%S.%N`.log"

# Phone
nexus4Name="Nexus4"
nexus4Mtp="Nexus 4/5/7/10 (.*), Google Inc (for LG Electronics/Samsung)"
nexus4Mount="/media/nexus4"
#nexus4Internal="Espace de stockage interne partagé"
nexus4Internal="Mémoire de stockage interne/"
nexus4Backup="$HOME/Greg/Informatique/Nexus4/Backup"

idol3Name="Idol3"
idol3Mtp="OneTouch Idol 3 small (MTP)"
idol3Mount="/media/idol3"
idol3Internal="Mémoire de stockage interne"
idol3SdCard="Carte SD"
idol3Backup="$HOME/Greg/Informatique/Idol3/Backup"

# Global variables
androidName=""
busNum=""
devNum=""
mountDir=""
backupDir=""
srcDirInternal=""
srcDirSdCard=""
catchOut=""

# lock
lockDir="/var/lock"
lockFile=$lockDir/$progName.lock
lockFd=200


# 
# Functions
#

# Detect the different Android phone
# return 1 for Nexus4/Idol3
# return 0 if none
busDevNum () {
    filter1=`echo "$catchOut" | awk -F ":" '{print $NF}'`
    echo "busDevNum function: filter=$filter1" |& tee -a $logF
    busNum=`echo $filter1 | awk -F "," '{print $1}' | sed 's/ *//'`
    devNum=`echo $filter1 | awk -F "," '{print $2}' | sed 's/ *//'`
    echo "busDevNum function: busNum=$busNum, devNum=$devNum" |& tee -a $logF
}


detect() {
    echo "Detect function" |& tee -a $logF
    catchOut=`jmtpfs -l`
    echo "Detect function: catchOut=$catchOut" |& tee -a $logF

    echo $catchOut | grep "$nexus4Mtp"
    if [ $? -eq 0 ]; then
        busDevNum
        androidName=$nexus4Name
        mountDir=$nexus4Mount
        backupDir=$nexus4Backup
        srcDirInternal=$nexus4Internal
        echo "$androidName detected with bus=$busNum and dev=$devNum" |& tee -a $logF
        return 1
    fi

    echo $catchOut | grep "$idol3Mtp"
    if [ $? -eq 0 ]; then
        busDevNum
        androidName=$idol3Name
        mountDir=$idol3Mount
        backupDir=$idol3Backup
        srcDirInternal=$idol3Internal
        srcDirSdCard=$idol3SdCard
        echo "$androidName detected with bus=$busNum and dev=$devNum" |& tee -a $logF
        return 1
    fi

    eexit "No Android detected.\nUnplug/Replug it.\nCheck if MTP mode is well activated."
}


# Synchronisation
syncDir() {
    echo "Sync src=$mountDir/$1 dest=$backupDir" |& tee -a $logF
    rsync -ra --progress --stats "$mountDir/$1" "$backupDir" |& tee -a $logF
}

sync() {
    if [ "$srcDirInternal" != "" ]; then
        syncDir "$srcDirInternal"
    fi
    if [ "$srcDirSdCard" != "" ]; then
        syncDir "$srcDirSdCard"
    fi
}


# Mount android phone
mount() {
    echo "Mount function" |& tee -a $logF

    ps aux | grep gvfsd-mtp | grep -v "grep"
    if [ $? -eq 0 ]; then
        echo "Kill automatic mtp mount point" |& tee -a $logF
        pkill -9 gvfsd-mtp
        sleep 2
    fi

    # Check if the mount point is not already mounted
    ls $mountDir
    if [ -d "$srcDir" ]; then
    umount
    fi

    echo "Mount jmtpfs -device=$busNum,$devNum $mountDir" |& tee -a $logF
    jmtpfs -device=$busNum,$devNum $mountDir

    # Check if no error during mount
    sleep 2
    echo "Test $mountDir/$srcDirInternal"
    if [ ! -d "$mountDir/$srcDirInternal" ]; then
        umount
        eexit "Android mount error ($mountDir).\nCheck if MTP mode is well activated."
    fi

}


# Umount android phone
umount() {
    echo "Umount $mountDir" |& tee -a $logF
    sleep 1
    fusermount -u $mountDir
}


lock() {
    local fd=${2:-$lockFd}

    # create lock file
    eval "exec $fd>$lockFile"

    # acquire the lock
    flock -n $fd \
        && return 0 \
        || return 1
}


eexit() {
    local error_str="$@"

    rm -f $lockFile
    echo $error_str |& tee -a $logF
    zenity --info --text="$error_str"
    exit 1
}


#
# Main script
#

main() {
    echo "Main script $progName" |& tee -a $logF

    exec 200>$lockFile
    lock $progName \
        || eexit "Only one instance of $progName can run at one time."
    
    detect
    if [ $? -eq 1 ]; then
        
        mount
        sync
        umount
    
        zenity --info --text="Congratulations !!!\n\nBackup directory = $backupDir.\nLog file = $logF"
    
    fi

    rm -f $lockFile
}

main

