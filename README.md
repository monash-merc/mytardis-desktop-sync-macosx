mytardis-desktop-sync-macosx
============================

PyObjC desktop application to allow Mac OS X users to store offline copies of their MyTardis data.

Building requires installing Xcode's command-line tools.

To build, use:

/usr/bin/python createMacApplication.py

If you have a Python installed from Python.Org, then you can use that instead of Apple's Python build (/usr/bin/python), 
but be aware that the PyObjC modules will be loaded from Apple's Python unless you have installed them in another Python.

Eventually, the aim is to schedule this to run regular syncs in the background, but for now, it only syncs after you
enter your credentials in the settings dialog and press Connect.

The application runs as a background Mac OS X application, i.e. even if you add its icon to the Dock, you won't see a 
light under the dock icon.  This is because we have set LSUIElement="1" in the application's Info.plist

After building, you can run the application from the command-line, using:

dist/MyTardis\ Desktop\ Sync.app/Contents/MacOS/MyTardis\ Desktop\ Sync

You should see a Tardis icon appear in your Mac Menu Bar's status bar.  When you first launch the application, the 
settings dialog will be displayed automatically.  It can be displayed again from the Tardis status icon's menu.

After you enter your MyTardis credentials, you will be given a list of your MyTardis experiments, and you will see a 
tick next to each experiment you already have a local copy of.  You can tick additional experiments to create a local
copy of them, and you can untick your already-synced experiments to delete your local copy of them.

The dialogs in this application are Cocoa dialogs, which can be edited in Xcode's Interface Builder.  The experiments
dialog has been connected to the application's NSUserDefaults object using bindings, as described in this tutorial:
http://daemonconstruction.blogspot.com.au/2011/11/simple-nstableview-application-with.html

A status icon is used to indicate whether the last sync was successful, or whether a sync is in progress:

![Image](images/Menu.png?raw=true)

A settings dialog allows the user to enter their MyTardis credentials:

![Image](images/Settings%20dialog.png?raw=true)

A list of experiments already synced is presented to the user:

![Image](images/Experiments%20already%20synced.png?raw=true)

The user can elect to add an additional experiment to the list of experiments to sync:

![Image](images/Experiment%20added%20to%20sync%20list.png?raw=true)

When the syncing is complete, the user will receive some notifications;

![Image](images/Notifications.png?raw=true)

