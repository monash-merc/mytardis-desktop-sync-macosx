# #!/usr/bin/python

# If you use the Apple-built Python (/usr/bin/python), then it should
# automatically find PyObjC and related Python modules in its path.  

# The PyObjC module isn't automatically found in the PYTHONPATH for my Python
# installation from Python.Org, so I will explicity add it to the python path:
import sys
sys.path.append('/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC')

import appdirs
import ConfigParser
import threading
import objc
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper
import time
import os
import subprocess
import tempfile
import traceback
import shutil
import webbrowser
import plistlib
import biplist
import unicodedata
import requests
from AlertDialog import alert
from UserExperimentsModel import UserExperimentsModel
from ExperimentDatasetsModel import ExperimentDatasetsModel
from DatasetFilesModel import DatasetFilesModel

# This Python script can't be run with "python desktopSync.py".
# You need to build an App bundle with py2app, using:
# python package_mac_version.py
# The executable will end up in:
# ./dist/MyTardis Desktop Sync.app/Contents/MacOS/MyTardis Desktop Sync
# and the Growl framework will end up in:
# ./dist/MyTardis Desktop Sync.app/Contents/Frameworks/Growl.framework
frameworkPath = '../Frameworks/Growl.framework'
myGrowlBundle = objc.loadBundle(
  "GrowlApplicationBridge",
  globals(),
  bundle_path = objc.pathForFramework(frameworkPath)
  )

windowController = None

def runApplescript(applescript):
    NSLog(unicode(applescript))
    tempAppleScriptFile=tempfile.NamedTemporaryFile(delete=False)
    tempAppleScriptFileName=tempAppleScriptFile.name
    tempAppleScriptFile.write(applescript)
    tempAppleScriptFile.close()
    proc = subprocess.Popen(['/usr/bin/osascript',tempAppleScriptFileName], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    stdout, stderr = proc.communicate()
    NSLog(unicode(stderr))
    NSLog(unicode(stdout))
    os.unlink(tempAppleScriptFileName)

    # Bring app to top
    NSApp.activateIgnoringOtherApps_(True)

class MenuMakerDelegate(NSObject):
    """
    This is a delegate for Growl, a required element of using the Growl
    service.
  
    There isn't a requirement that delegates actually 'do' anything, but
    in this case, it creates a menulet with a Tardis icon.
    """
    statusbar = None
    state = 'idle'

    def applicationDidFinishLaunching_(self, notification):

        """
        Set up the menu and our menu items.
        """

        statusbar = NSStatusBar.systemStatusBar()
        # Create the statusbar item
        #self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem = statusbar.statusItemWithLength_(-1)

        self.statusitem.setHighlightMode_(1)  # Let it highlight upon clicking
        self.statusitem.setToolTip_('MyTardis Desktop Sync')   # Set a tooltip
        #self.statusitem.setTitle_('MyTardis')   # Set an initial title

        self.icon = NSImage.alloc().initByReferencingFile_('tardis.png')
        self.icon.setScalesWhenResized_(True)
        self.icon.setSize_((20, 20))
        # We can change the icon later if the status changes to "syncing".
        self.statusitem.setImage_(self.icon)

        # Build a very simple menu
        self.menu = NSMenu.alloc().init()

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
          'Open MyTardis in web browser',
          'onOpenMyTardisInWebBrowser:',
          ''
        )
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
          'Open local MyTardis folder',
          'onOpenLocalMyTardisFolder:',
          ''
        )
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
          'Settings...',
          'onOpenSettings:',
          ''
        )
        self.menu.addItem_(menuitem)

        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
          'Quit',
          'terminate:',
          ''
        )
        self.menu.addItem_(menuitem)

        # Bind it to the status item
        self.statusitem.setMenu_(self.menu)

    def onOpenMyTardisInWebBrowser_(self,notification):
        webbrowser.open("https://mytardis.massive.org.au/")

    def onOpenLocalMyTardisFolder_(self,notification):
        NSLog(u"onOpenLocalMyTardisFolder")
        self.localFolder = str(windowController.localFolderField.stringValue())
        if os.path.exists(self.localFolder):
            NSLog(u"Path exists.")
            os.system('open "' + self.localFolder + '"')
        else:
            NSLog(u"Path doesn't exist.")
            alert("MyTardis Desktop Sync", "Path " + self.localFolder + " doesn't exist!", ["OK"])

    def onOpenSettings_(self,notification):
        # Bring app to top
        NSApp.activateIgnoringOtherApps_(True)
        windowController.usernameField.becomeFirstResponder()
        sender = None
        windowController.settingsPanel.makeKeyAndOrderFront_(sender)
    
class rcGrowl(NSObject):

    """
    rcGrowl registers this app with Growl to send out notifications 
    on behalf of the user and do 'something' with the results when a 
    notification has been clicked.
  
    For additional information on what the what is going on
    please refer to the growl documentation:
  
    http://growl.info/documentation/developer/implementing-growl.php
    """

    def rcSetDelegate(self):
        GrowlApplicationBridge.setGrowlDelegate_(self)

    def registrationDictionaryForGrowl(self):

        """
        http://growl.info/documentation/developer/implementing-growl.php#registration
        """

        return {
          u'ApplicationName'    :   'rcGrowlMacTidy',
          u'AllNotifications'   :   ['growlNotification1'],
          u'DefaultNotifications' :   ['growlNotification1'],
          u'NotificationIcon'   :   None,
        } 

    # don't know if it is working or not
    def applicationNameForGrowl(self):
        """ 
        Identifies the application.
        """
        return 'rcGrowlMacTidy'

    def applicationIconDataForGrowl(self):
        """
        Custom icon to display in the notification.
        This doesn't seem to work, but we can just create
        a Tardis.icns bundle using Img2icns and add it 
        to the Info.plist in the create_mac_bundle.py 
        script used with py2app.
        """
        icon = NSImage.alloc().init()
        icon = icon.initWithContentsOfFile_(u'tardis.png')
        return icon

    def growlNotificationWasClicked_(self, ctx):

        """
        callback for onClick event
        """
        #NSLog(u"we got a click! " + str(time.time()) + " >>> " + str(ctx) + " <<<\n")

    def growlNotificationTimedOut_(self, ctx):

        """ 
        callback for timing out
        """
        #NSLog(u"We timed out" + str(ctx) + "\n")

    def growlIsReady(self):

        """
        Informs the delegate that GrowlHelperApp was launched
        successfully. Presumably if it's already running it
        won't need to run it again?
        """
        #NSLog(u"growl IS READY")


class MyTardisGrowlTest(NSWindowController):

    settingsPanel = objc.IBOutlet()
    serverAddressField = objc.IBOutlet()
    localFolderField = objc.IBOutlet()
    usernameField = objc.IBOutlet()
    passwordField = objc.IBOutlet()

    experimentsPanel = objc.IBOutlet()

    def awakeFromNib(self):
        self.serverAddressField.setStringValue_("https://mytardis.massive.org.au/")
        localFolder = os.path.join(os.path.expanduser('~'),"MyTardis")
        self.localFolderField.setStringValue_(localFolder)
        if globalConfig.has_section("Global Preferences"):
            if globalConfig.has_option("Global Preferences", "username"):
                username = globalConfig.get("Global Preferences", "username")
                self.usernameField.setStringValue_(username)

        self.notificationCenter = NSNotificationCenter.defaultCenter()
        self.notificationCenter.addObserver_selector_name_object_(self, "createLocalFolderAndAddToSidebar:", 'createLocalFolderAndAddToSidebar', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "getRemoteExperimentsForUser:", 'getRemoteExperimentsForUser', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "scanLocalExperimentFolders:", 'scanLocalExperimentFolders', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "askUserWhichExperimentsToSync:", 'askUserWhichExperimentsToSync', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "deleteUnusedLocalExperimentFolders:", 'deleteUnusedLocalExperimentFolders', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "getDatasetsForExperiments:", 'getDatasetsForExperiments', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "getDatasetFilesForDatasets:", 'getDatasetFilesForDatasets', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "createLocalExperimentFolders:", 'createLocalExperimentFolders', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "createLocalDatasetFolders:", 'createLocalDatasetFolders', None)
        self.notificationCenter.addObserver_selector_name_object_(self, "downloadDatasetFiles:", 'downloadDatasetFiles', None)

        self.menuMakerDelegate = NSApplication.sharedApplication().delegate()

        self.tardisTickStatusBarIcon = NSImage.alloc().initByReferencingFile_('tardis_tick.png')
        self.tardisTickStatusBarIcon.setScalesWhenResized_(True)
        self.tardisTickStatusBarIcon.setSize_((20, 20))
    
        self.tardisCrossStatusBarIcon = NSImage.alloc().initByReferencingFile_('tardis_cross.png')
        self.tardisCrossStatusBarIcon.setScalesWhenResized_(True)
        self.tardisCrossStatusBarIcon.setSize_((20, 20))
    
        self.tardisRefreshStatusBarIcon = NSImage.alloc().initByReferencingFile_('tardis_refresh.png')
        self.tardisRefreshStatusBarIcon.setScalesWhenResized_(True)
        self.tardisRefreshStatusBarIcon.setSize_((20, 20))

    @objc.IBAction
    def onConnect_(self, sender):
        # I've noticed a bug where after pressing Connect on the Settings panel,
        # and allowing the MyTardis connections to be made, if you open the
        # Settings panel again, this method gets called immediately when the
        # panel is displayed, even though the Connect button hasn't been pressed
        # yet.  This could be because this method is doing too much in the GUI
        # thread - it really should be spawning a separate thread.  I have
        # lessened the problem by ensuring that the password field is cleared
        # immediately after it is used - this will prevent the time-consuming
        # part of this method from being accidentally executed a second time.

        if (hasattr(self,'onConnectRunning') and self.onConnectRunning):
            return
        self.onConnectingRunning = True

        self.mytardisUrl = self.serverAddressField.stringValue()
        self.username = self.usernameField.stringValue()
        self.password = self.passwordField.stringValue()
        if self.password.strip()=="":
            alert("MyTardis Desktop Sync", "Please enter your password.", ["OK"])
            windowController.passwordField.becomeFirstResponder()
            return

        globalConfig.set("Global Preferences", "username", self.username)

        with open(globalPreferencesFilePath, 'wb') as globalPreferencesFileObject:
            globalConfig.write(globalPreferencesFileObject)

        self.passwordField.setStringValue_("")
        sender = None
        self.settingsPanel.performClose_(sender)

        self.onConnectingRunning = False
        self.notificationCenter.postNotificationName_object_userInfo_('createLocalFolderAndAddToSidebar', None, None)

    @objc.signature('v@:@')
    def createLocalFolderAndAddToSidebar_(self,sender):

        if (hasattr(self,'createLocalFolderAndAddToSidebarRunning') and self.createLocalFolderAndAddToSidebarRunning):
            return
        self.createLocalFolderAndAddToSidebarRunning = True

        self.localFolder = self.localFolderField.stringValue()
        if not os.path.exists(self.localFolder):
            try:
                os.mkdir(self.localFolder)
            except:
                errorMessage = "Failed to create directory: " + self.localFolder
                alert("MyTardis Desktop Sync", errorMessage, ["OK"])
                windowController.settingsPanel.makeKeyAndOrderFront_(sender)
                self.createLocalFolderAndAddToSidebarRunning = False
                return

        # Check whether our local MyTardis folder has already been added to the
        # Finder's sidebar:

        self.localFolderIsInFinderSidebar = False
        sidebarPlistFilePath = os.path.join(os.path.expanduser('~'),"Library/Preferences/com.apple.sidebarlists.plist")
        if os.path.exists(sidebarPlistFilePath):
            sidebarPlist = None
            try:
                sidebarPlist = biplist.readPlist(sidebarPlistFilePath)
            except InvalidPlistException, e:
                NSLog(u"Invalid plist.")
            except NotBinaryPlistException, e:
                sidebarPlist = plistlib.readPlist(sidebarPlistFilePath)

            localFolderSearchString = unicodedata.normalize('NFKD', self.localFolder.strip("/")).encode('ascii','ignore')
            favouriteVolumesList = sidebarPlist['favorites']['VolumesList']
            for volume in favouriteVolumesList:
                if 'Alias' in volume.keys() and localFolderSearchString in volume['Alias']:
                    NSLog(u"Found path in alias: Name = " + volume['Name'])
                    self.localFolderIsInFinderSidebar = True

        if not self.localFolderIsInFinderSidebar:
            # The following applescript adds the local folder to the Finder's sidebar.

            applescript = """
tell application "Finder"
    activate
    set myFolder to POSIX file """

            applescript = applescript + '"' + self.localFolder + '"'
            applescript = applescript + """
    select myFolder
    tell application "System Events"
        # Add folder to Finder sidebar
        keystroke "t" using command down
    end tell
    #   close front Finder window
end tell
"""

            runApplescript(applescript)

        self.createLocalFolderAndAddToSidebarRunning = False
        self.notificationCenter.postNotificationName_object_userInfo_('getRemoteExperimentsForUser', None, None)

    @objc.signature('v@:@')
    def getRemoteExperimentsForUser_(self,sender):

        if (hasattr(self,'getRemoteExperimentsForUserRunning') and self.getRemoteExperimentsForUserRunning):
            return
        self.getRemoteExperimentsForUserRunning = True

        self.userExperimentsModel = UserExperimentsModel(self.mytardisUrl,self.username,self.password)
        self.userExperimentsModel.parseMyTardisExperimentList()
        errorMessage = self.userExperimentsModel.getUnhandledExceptionMessage()
        if errorMessage is not None:
            NSLog(unicode(errorMessage))
            windowController.settingsPanel.makeKeyAndOrderFront_(sender)
            self.menuMakerDelegate.statusitem.setImage_(self.tardisCrossStatusBarIcon)
            alert("MyTardis Desktop Sync", errorMessage, ["OK"])
            self.getRemoteExperimentsForUserRunning = False
            return

        self.getRemoteExperimentsForUserRunning = False
        self.notificationCenter.postNotificationName_object_userInfo_('scanLocalExperimentFolders', None, None)

    @objc.signature('v@:@')
    def scanLocalExperimentFolders_(self,sender):

        if (hasattr(self,'scanLocalExperimentFoldersRunning') and self.scanLocalExperimentFoldersRunning):
            return
        self.scanLocalExperimentFoldersRunning = True

        self.localExperimentFolders = {}
        for experimentID,experiment in self.userExperimentsModel.getExperiments().iteritems():
            if os.path.exists(os.path.join(self.localFolder, experiment.getDirectoryName())):
                self.localExperimentFolders[experimentID] = experiment.getDirectoryName()
            else:
                self.localExperimentFolders[experimentID] = None

        self.scanLocalExperimentFoldersRunning = False
        self.notificationCenter.postNotificationName_object_userInfo_('askUserWhichExperimentsToSync', None, None)

    @objc.signature('v@:@')
    def askUserWhichExperimentsToSync_(self,sender):

        if (hasattr(self,'askUserWhichExperimentsToSyncRunning') and self.askUserWhichExperimentsToSyncRunning):
            return
        self.askUserWhichExperimentsToSyncRunning = True

        experiments = []
        for experimentID in self.userExperimentsModel.getExperimentIDs():
            experiments.append(dict(
                optin = (self.localExperimentFolders[experimentID]!=None),
                experimentID = experimentID,
                experimentName = self.userExperimentsModel.getExperimentTitles()[experimentID]
                ))
        NSUserDefaults.standardUserDefaults().setObject_forKey_(experiments,'experiments')

        if NSApplication.sharedApplication().runModalForWindow_(self.experimentsPanel) == NSOKButton:
            NSLog(u"experimentsPanel OK")
        else:
            NSLog(u"experimentsPanel Cancel")
            self.askUserWhichExperimentsToSyncRunning = False
            return

        experimentsPlistArray = NSUserDefaults.standardUserDefaults().objectForKey_('experiments')
        for experimentDict in experimentsPlistArray:
            experiment = self.userExperimentsModel.getExperiment(experimentDict['experimentID'])
            experiment.setOptIn(experimentDict['optin'])

        self.askUserWhichExperimentsToSyncRunning = False
        self.notificationCenter.postNotificationName_object_userInfo_('deleteUnusedLocalExperimentFolders', None, None)

    @objc.signature('v@:@')
    def deleteUnusedLocalExperimentFolders_(self,sender):

        if (hasattr(self,'deleteUnusedLocalExperimentFoldersRunning') and self.deleteUnusedLocalExperimentFoldersRunning):
            return
        self.deleteUnusedLocalExperimentFoldersRunning = True

        localFolderSubdirectoriesToDelete = []

        localFolderSubdirectories = os.walk(self.localFolder).next()[1]
        for localFolderSubdirectory in localFolderSubdirectories:
            if not " - " in localFolderSubdirectory:
                continue
            localFolderExperimentID = os.path.split(localFolderSubdirectory)[1].split(" - ")[0]
            if self.userExperimentsModel.getExperiment(localFolderExperimentID)!=None and \
                self.userExperimentsModel.getExperiment(localFolderExperimentID).getOptIn()==False:
                    localFolderSubdirectoriesToDelete.append(self.userExperimentsModel.getExperiment(localFolderExperimentID).getDirectoryName())

        if len(localFolderSubdirectoriesToDelete)>0:
            message = """
WARNING: The following experiment folders:

"""

            for localFolderSubdirectoryToDelete in localFolderSubdirectoriesToDelete:
                message = message + localFolderSubdirectoryToDelete + "\n"

            message = message + """
will be deleted from:

"""
            message = message + self.localFolder

            okButtonID = NSAlertFirstButtonReturn
            cancelButtonID = NSAlertSecondButtonReturn
            buttonPressed = alert("MyTardis Desktop Sync", message, ["OK","Cancel"])
            if buttonPressed==okButtonID:
                NSLog(u"OK button pressed.")
                for localFolderSubdirectoryToDelete in localFolderSubdirectoriesToDelete:
                    shutil.rmtree(os.path.join(self.localFolder,localFolderSubdirectoryToDelete))
            else:
                NSLog(u"Cancel button pressed.")
                windowController.settingsPanel.makeKeyAndOrderFront_(sender)
                self.deleteUnusedLocalExperimentFoldersRunning = False
                return

        self.deleteUnusedLocalExperimentFoldersRunning = False
        self.notificationCenter.postNotificationName_object_userInfo_('getDatasetsForExperiments', None, None)

    @objc.signature('v@:@')
    def getDatasetsForExperiments_(self,sender):

        if (hasattr(self,'getDatasetsForExperimentsRunning') and self.getDatasetsForExperimentsRunning):
            return
        self.getDatasetsForExperimentsRunning = True

        self.menuMakerDelegate.statusitem.setImage_(self.tardisRefreshStatusBarIcon)

        def getDatasetsForExperimentsThread():
            pool = NSAutoreleasePool.alloc().init()
            self.countTotalRemoteDatasetsInOptedInExperiments = 0
            self.experimentDatasetsModel = {}
        
            for experimentID,experiment in self.userExperimentsModel.getExperiments().iteritems():
                if not experiment.getOptIn():
                    continue
                self.experimentDatasetsModel[experimentID] = ExperimentDatasetsModel(self.mytardisUrl,self.username,self.password,experimentID)
                self.experimentDatasetsModel[experimentID].parseMyTardisDatasetList()
                errorMessage = self.experimentDatasetsModel[experimentID].getUnhandledExceptionMessage()
                if errorMessage is not None:
                    NSLog(u"My Exception: " + unicode(errorMessage))
                    self.menuMakerDelegate.statusitem.performSelectorOnMainThread_withObject_waitUntilDone_("setImage:",self.tardisCrossStatusBarIcon,0)

                    #alert("MyTardis Desktop Sync", errorMessage, ["OK"])
                    alertPanel = NSAlert.alloc().init()
                    alertPanel.setMessageText_("MyTardis Desktop Sync")
                    alertPanel.setInformativeText_(errorMessage)
                    alertPanel.setAlertStyle_(NSInformationalAlertStyle)
                    alertPanel.addButtonWithTitle_("OK")
                    NSApp.activateIgnoringOtherApps_(True)
                    alertPanel.performSelectorOnMainThread_withObject_waitUntilDone_("runModal",None,1)
                    windowController.settingsPanel.makeKeyAndOrderFront_(sender)
                    self.getDatasetsForExperimentsRunning = False
                    return
                self.countTotalRemoteDatasetsInOptedInExperiments = self.countTotalRemoteDatasetsInOptedInExperiments + self.experimentDatasetsModel[experimentID].getNumberOfDatasets()
  
            self.getDatasetsForExperimentsRunning = False
            self.notificationCenter.postNotificationName_object_userInfo_('getDatasetFilesForDatasets', None, None)

        thread = threading.Thread(target = getDatasetsForExperimentsThread)
        thread.start()

    @objc.signature('v@:@')
    def getDatasetFilesForDatasets_(self,sender):

        if (hasattr(self,'getDatasetFilesForDatasetsRunning') and self.getDatasetFilesForDatasetsRunning):
            return
        self.getDatasetFilesForDatasetsRunning = True

        def getDatasetFilesForDatasetsThread():
            pool = NSAutoreleasePool.alloc().init()
            self.countTotalRemoteDatasetFilesInOptedInExperiments = 0
            self.experimentDatasetFilesModel = {}
        
            for experimentID,experiment in self.userExperimentsModel.getExperiments().iteritems():
                if not experiment.getOptIn():
                    continue
                self.experimentDatasetFilesModel[experimentID] = dict()
                for datasetID,dataset in self.experimentDatasetsModel[experimentID].getDatasets().iteritems():
                    self.experimentDatasetFilesModel[experimentID][datasetID] = DatasetFilesModel(self.mytardisUrl,self.username,self.password,datasetID)
                    self.experimentDatasetFilesModel[experimentID][datasetID].parseMyTardisDatafileList()
                errorMessage = self.experimentDatasetFilesModel[experimentID][datasetID].getUnhandledExceptionMessage()
                if errorMessage is not None:
                    NSLog(unicode(errorMessage))
                    self.menuMakerDelegate.statusitem.performSelectorOnMainThread_withObject_waitUntilDone_("setImage:",self.tardisCrossStatusBarIcon,0)
                    #alert("MyTardis Desktop Sync", errorMessage, ["OK"])
                    alertPanel = NSAlert.alloc().init()
                    alertPanel.setMessageText_("MyTardis Desktop Sync")
                    alertPanel.setInformativeText_(errorMessage)
                    alertPanel.setAlertStyle_(NSInformationalAlertStyle)
                    alertPanel.addButtonWithTitle_("OK")
                    NSApp.activateIgnoringOtherApps_(True)
                    alertPanel.performSelectorOnMainThread_withObject_waitUntilDone_("runModal",None,1)
                    windowController.settingsPanel.makeKeyAndOrderFront_(sender)
                    self.getDatasetFilesForDatasetsRunning = False
                    return
                self.countTotalRemoteDatasetFilesInOptedInExperiments = self.countTotalRemoteDatasetFilesInOptedInExperiments + self.experimentDatasetFilesModel[experimentID][datasetID].getNumberOfDatafiles()

            self.getDatasetFilesForDatasetsRunning = False
            self.notificationCenter.postNotificationName_object_userInfo_('createLocalExperimentFolders', None, None)

        thread = threading.Thread(target = getDatasetFilesForDatasetsThread)
        thread.start()

    @objc.signature('v@:@')
    def createLocalExperimentFolders_(self,sender):

        if (hasattr(self,'createLocalExperimentFoldersRunning') and self.createLocalExperimentFoldersRunning):
            return
        self.createLocalExperimentFoldersRunning = True

        def createLocalExperimentFoldersThread():
            pool = NSAutoreleasePool.alloc().init()
            for experimentID,experiment in self.userExperimentsModel.getExperiments().iteritems():
                if not experiment.getOptIn():
                    continue
                if not os.path.exists(os.path.join(self.localFolder, experiment.getDirectoryName())):
                    try:
                        os.mkdir(os.path.join(self.localFolder, experiment.getDirectoryName()))
                    except:
                        NSLog(u"Failed to create directory: " + os.path.join(self.localFolder, experiment.getDirectoryName()))
                    try:
                        # Force finder window to refresh:
                        #os.system('open "' + self.localFolder + '"')
                        # The following will give an error if there is no Finder window open,
                        # but if the user has the local folder open in Finder, then this
                        # will force the window to refresh after each experiment is added.
                        applescript = 'tell application "Finder" to delete (make new folder at (front window))'
                        runApplescript(applescript)
                    except:
                        NSLog(unicode(traceback.format_exc()))
        
            self.createLocalExperimentFoldersRunning = False
            self.notificationCenter.postNotificationName_object_userInfo_('createLocalDatasetFolders', None, None)
        
        thread = threading.Thread(target = createLocalExperimentFoldersThread)
        thread.start()

    @objc.signature('v@:@')
    def createLocalDatasetFolders_(self,sender):

        if (hasattr(self,'createLocalDatasetFoldersRunning') and self.createLocalDatasetFoldersRunning):
            return
        self.createLocalDatasetFoldersRunning = True

        def createLocalDatasetFoldersThread():
            pool = NSAutoreleasePool.alloc().init()
            countLocalDatasetFoldersCreated = 0

            for experimentID,experiment in self.userExperimentsModel.getExperiments().iteritems():
                if not experiment.getOptIn():
                    continue
                for datasetID,dataset in self.experimentDatasetsModel[experimentID].getDatasets().iteritems():
                    if not os.path.exists(os.path.join(self.localFolder, experiment.getDirectoryName(), dataset.getDirectoryName())):
                        try:
                            os.mkdir(os.path.join(self.localFolder, experiment.getDirectoryName(), dataset.getDirectoryName()))
                            countLocalDatasetFoldersCreated = countLocalDatasetFoldersCreated + 1
                        except:
                            NSLog(u"Failed to create directory: " + os.path.join(self.localFolder, experiment.getDirectoryName(), dataset.getDirectoryName()))

            if countLocalDatasetFoldersCreated > 0:
                isSticky = False
                GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(
                  "MyTardis Desktop Sync Client",
                  str(countLocalDatasetFoldersCreated) + " data set folder(s) were created in " + self.localFolder,
                  "growlNotification1", None, 0, isSticky, "This will be the argument to the context callback")

            self.createLocalDatasetFoldersRunning = False
            self.notificationCenter.postNotificationName_object_userInfo_('downloadDatasetFiles', None, None)

        thread = threading.Thread(target = createLocalDatasetFoldersThread)
        thread.start()

    @objc.signature('v@:@')
    def downloadDatasetFiles_(self,sender):

        if (hasattr(self,'downloadDatasetFilesRunning') and self.downloadDatasetFilesRunning):
            return
        self.downloadDatasetFilesRunning = True

        def downloadDatasetFilesThread():
            pool = NSAutoreleasePool.alloc().init()

            try:
                session = requests.session()
                r = session.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
                if r.status_code==200:
                    NSLog(u"MyTardis authentication succeeded for username: " + self.username)
                    pass
                else:
                    # raise Exception("MyTardis authentication failed for username: " + self.username)
                    # Combining Python try/except with Objective-C try/catch is complicated.
                    self.unhandledExceptionMessage = "MyTardis authentication failed for username: " + self.username
                    NSLog(unicode(self.unhandledExceptionMessage))
                    self.downloadDatasetFilesRunning = False
                    return
            except:
                NSLog(unicode(traceback.format_exc()))

            countDatafilesDownloaded = 0

            exceptionOccurred = False
            for experimentID,experiment in self.userExperimentsModel.getExperiments().iteritems():
                if not experiment.getOptIn():
                    continue
                NSLog(u"experiment.getDirectoryName() = " + experiment.getDirectoryName())
                for datasetID,dataset in self.experimentDatasetsModel[experimentID].getDatasets().iteritems():
                    NSLog(u"dataset.getDirectoryName() = " + dataset.getDirectoryName())
                    for datafileID,datafile in self.experimentDatasetFilesModel[experimentID][datasetID].getDatafiles().iteritems():
                        if datafile.getFileName() is None:
                            continue
                        NSLog(u"datafile.getFileName() = " + datafile.getFileName())
                        pathToDownloadTo = os.path.join(self.localFolder, experiment.getDirectoryName(), dataset.getDirectoryName(), datafile.getFileName())
                        NSLog(u"pathToDownloadTo = " + pathToDownloadTo)
                        # We really should do an MD5 hash check here, not just check whether the file exists:
                        if not os.path.exists(pathToDownloadTo):
                            NSLog(u"Data file doesn't exist locally. Downloading from server.")
                            datafile.downloadTo(pathToDownloadTo,session)
                            errorMessage = datafile.getUnhandledExceptionMessage()
                            if errorMessage is not None:
                                NSLog(unicode(errorMessage))
                                exceptionOccurred = True
                                # For now, we will allow the sync-ing to continue even if it fails for some data file(s).
                            else:
                                countDatafilesDownloaded = countDatafilesDownloaded + 1
                        else:
                            NSLog(u"Data file already exists locally. Not downloading from server.")

            try:
                session.close()
            except:
                NSLog(unicode(traceback.format_exc()))

            if exceptionOccurred:
                self.menuMakerDelegate.statusitem.performSelectorOnMainThread_withObject_waitUntilDone_("setImage:",self.tardisCrossStatusBarIcon,0)
            else:
                self.menuMakerDelegate.statusitem.performSelectorOnMainThread_withObject_waitUntilDone_("setImage:",self.tardisTickStatusBarIcon,0)

            if countDatafilesDownloaded > 0:
                isSticky = False
                GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(
                  "MyTardis Desktop Sync Client",
                  str(countDatafilesDownloaded) + " data files were downloaded from MyTardis.",
                  "growlNotification1", None, 0, isSticky, "This will be the argument to the context callback")

            self.downloadDatasetFilesRunning = False

        thread = threading.Thread(target = downloadDatasetFilesThread)
        thread.start()

    @objc.IBAction
    def onExperimentsPanelOKButtonClicked_(self, sender):
        NSApplication.sharedApplication().stopModalWithCode_(NSOKButton)
        self.experimentsPanel.performClose_(sender)

    @objc.IBAction
    def onExperimentsPanelCancelButtonClicked_(self, sender):
        NSApplication.sharedApplication().stopModalWithCode_(NSCancelButton)
        self.experimentsPanel.performClose_(sender)

    @objc.IBAction
    def onBrowse_(self, sender):
        NSLog(u"Browse button pressed!")
        panel = NSOpenPanel.openPanel()
        panel.setCanCreateDirectories_(True)
        panel.setCanChooseDirectories_(True)
        panel.setCanChooseFiles_(False)
        if panel.runModal() == NSOKButton:
            NSLog(unicode(panel.filename()))
            self.localFolderField.setStringValue_(panel.filename())

    @objc.IBAction
    def onCancelFromExperimentsPanel_(self, sender):
        NSLog(u"onCancelFromExperimentsPanel_")
        self.experimentsPanel.performClose_(sender)


if __name__ == "__main__":
    appDirs = appdirs.AppDirs("MyTardis Desktop Sync", "Monash University")
    appUserDataDir = appDirs.user_data_dir
    # Add trailing slash:
    appUserDataDir = os.path.join(appUserDataDir,"")
    if not os.path.exists(appUserDataDir):
        os.makedirs(appUserDataDir)

    sys.modules[__name__].globalConfig = ConfigParser.RawConfigParser(allow_no_value=True)
    globalConfig = sys.modules[__name__].globalConfig
    sys.modules[__name__].globalPreferencesFilePath = os.path.join(appUserDataDir,"Global Preferences.cfg")
    globalPreferencesFilePath = sys.modules[__name__].globalPreferencesFilePath
    if os.path.exists(globalPreferencesFilePath):
        globalConfig.read(globalPreferencesFilePath)
    if not globalConfig.has_section("Global Preferences"):
        globalConfig.add_section("Global Preferences")

    # set up system statusbar GUI
    app = NSApplication.sharedApplication()
    delegate = MenuMakerDelegate.alloc().init()
    app.setDelegate_(delegate)

    # set up growl delegate
    rcGrowlDelegate=rcGrowl.new()
    rcGrowlDelegate.rcSetDelegate()

    windowController = MyTardisGrowlTest.alloc().initWithWindowNibName_("MyTardisGrowlTest")

    sender = None
    windowController.showWindow_(sender)
    #windowController.settingsPanel.orderOut_(sender)
    windowController.usernameField.becomeFirstResponder()
    windowController.settingsPanel.makeKeyAndOrderFront_(sender)

    # Bring app to top
    NSApp.activateIgnoringOtherApps_(True)

    AppHelper.runEventLoop()

