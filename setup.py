"""
A distutils script to make a standalone .app of the MyTardis Desktop Sync script.

   python setup.py py2app

"""

from setuptools import setup

resource_files=["Tardis.icns", "icons/tardis.png", "icons/tardis_tick.png", "icons/tardis_cross.png", "icons/tardis_refresh.png", "MyTardisGrowlTest.xib"]

setup(
    options=dict(py2app=dict(
        #arch='i386',
        #frameworks=['../Frameworks/Growl.framework'],
        plist=dict(
            CFBundleDevelopmentRegion="English",
            CFBundleDisplayName="MyTardis Desktop Sync",
            CFBundleExecutable="MyTardis Desktop Sync",
            CFBundleIdentifier="au.org.massive.cvl.mytardis.desktopsync",
            CFBundleName="MyTardis Desktop Sync",
            CFBundlePackageType="APPL",
            CFBundleIconFile="Tardis.icns",
            LSUIElement="1",
            CFBundleVersion="Version 0.0.1"
            )
        )
    ),
    name="MyTardis Desktop Sync",
    setup_requires=["py2app"],
    app=['desktopSync.py'],
    data_files=resource_files
)
