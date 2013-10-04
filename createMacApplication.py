# Builds dist/MyTardis Desktop Sync.app

import os
import sys
import tempfile
import commands
import subprocess
import shutil

PERFORM_CODE_SIGNING = False
BUILD_DMG = False

if PERFORM_CODE_SIGNING:
    defaultCertificateName = "Developer ID Application: James Wettenhall"
    certificateName = defaultCertificateName

    # The digital signing parts of this  script 
    # assume that you only have one
    # Developer ID Application certificate in
    # your key chain.  You need to have a private
    # key attached to the certificate in your key
    # chain, so generally you will need to create
    # a certificate-signing request on the build
    # machine, upload it to the Apple Developer
    # Portal, and download a new certificate with
    # a private key attached.

    # If you want to obtain your own Apple code-signing 
    # certificate, you will probably need to pay
    # $99 per year to join the Apple Developer Program.
    # So far, I haven't had any luck with using a 
    # generic (non-Apple) code-signing certificate.

    cmd = 'certtool y | grep "Developer ID Application"'
    print cmd
    certificateLine = commands.getoutput(cmd)
    print "certificateLine: " + certificateLine
    certificateName = certificateLine.split(": ",1)[1]
    print "certificateName: " + certificateName

if BUILD_DMG:
    INCLUDE_APPLICATIONS_SYMBOLIC_LINK = True
    ATTEMPT_TO_SET_ICON_SIZE_IN_DMG = True
    ATTEMPT_TO_LAY_OUT_ICONS_ON_DMG = True
    ATTEMPT_TO_SET_BACKGROUND_IMAGE = True

    if len(sys.argv) < 2:
        print "Usage: /usr/bin/python package_mac_version.py <version>"
        sys.exit(1)

    version = sys.argv[1]

os.system('rm -fr build/*')
os.system('rm -fr dist/*')

# Build "dist/MyTardis Desktop Sync.app"
#os.system('/usr/bin/python setup.py py2app')
os.system('python setup.py py2app')
shutil.copytree(r'./Frameworks/Growl.framework', r'dist/MyTardis Desktop Sync.app/Contents/Frameworks/Growl.framework')
os.system('open dist/')
print "\nYou can run the bundled application from the command-line using:\n\n" + \
        "dist/MyTardis\\ Desktop\\ Sync.app/Contents/MacOS/MyTardis\\ Desktop\\ Sync\n"

if PERFORM_CODE_SIGNING:
    # Digitally sign application:
    cmd = "CODESIGN_ALLOCATE=/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/codesign_allocate"
    print cmd
    os.environ['CODESIGN_ALLOCATE'] = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/codesign_allocate'
    # The bundle identifier (au.org.massive.cvl.mytardis.desktopsync) referenced below is set in setup.py:
    cmd = 'codesign --force -i "au.org.massive.cvl.mytardis.desktopsync" --sign "%s" --verbose=4 dist/MyTardis\ Desktop\ Sync.app' % (certificateName)
    print cmd
    os.system(cmd)
    cmd = 'codesign -vvvv dist/MyTardis\ Desktop\ Sync.app/'
    print cmd
    os.system(cmd)
    cmd = 'spctl --assess --raw --type execute --verbose=4 dist/MyTardis\ Desktop\ Sync.app/'
    print cmd
    os.system(cmd)

if not BUILD_DMG:
    print "Exiting early. Not building DMG."
    os._exit(0)

# Build DMG (disk image) :

source = os.path.join(os.getcwd(),'dist')
applicationName = "MyTardis Desktop Sync"
title = applicationName + " " + version
size="80000"
finalDmgName = applicationName + " " + version

tempDmgFile=tempfile.NamedTemporaryFile(prefix=finalDmgName+"_",suffix=".dmg",delete=True)
tempDmgFileName=tempDmgFile.name
tempDmgFile.close()

backgroundPictureFileName = "dmgBackgroundMacOSX.png"

cmd = 'hdiutil create -srcfolder "%s" -volname "%s" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size %sk "%s"' % (source,title,size,tempDmgFileName)
print cmd
os.system(cmd)

cmd = "hdiutil attach -readwrite -noverify -noautoopen \"%s\" | egrep '^/dev/' | sed 1q | awk '{print $1}'" % (tempDmgFileName)
print cmd
device = commands.getoutput(cmd)

cmd = 'sleep 2'
print cmd
os.system(cmd)

cmd = 'mkdir "/Volumes/%s/.background/"' % (title)
print cmd
os.system(cmd)

cmd = 'cp %s "/Volumes/%s/.background/"' % (backgroundPictureFileName,title)
print cmd
os.system(cmd)

if INCLUDE_APPLICATIONS_SYMBOLIC_LINK:
    cmd = 'ln -s /Applications/ "/Volumes/' + title + '/Applications"'
    print cmd
    os.system(cmd)

applescript = """
tell application "Finder"
     tell disk "%s"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set theViewOptions to the icon view options of container window
""" % (title)
if ATTEMPT_TO_SET_ICON_SIZE_IN_DMG:
    applescript = applescript + """
           set icon size of theViewOptions to 96
           delay 1
"""
if ATTEMPT_TO_LAY_OUT_ICONS_ON_DMG:
    applescript = applescript + """
           set the bounds of container window to {400, 100, 885, 430}
           delay 1
           set arrangement of theViewOptions to not arranged
           delay 1
           set file_list to every file
           repeat with file_object in file_list
               if the name of file_object ends with ".app" then
                   set the position of file_object to {120, 163}
               else if the name of file_object is "Applications" then
                   set the position of file_object to {375, 163}
               end if
           end repeat
           delay 1
"""
if ATTEMPT_TO_SET_BACKGROUND_IMAGE:
    applescript = applescript + """
           set background picture of theViewOptions to file ".background:%s"
""" % (backgroundPictureFileName)
applescript = applescript + """
           delay 1
           close
           open
           update without registering applications
           delay 5
     end tell
   end tell
"""
print applescript
tempAppleScriptFile=tempfile.NamedTemporaryFile(delete=False)
tempAppleScriptFileName=tempAppleScriptFile.name
tempAppleScriptFile.write(applescript)
tempAppleScriptFile.close()
proc = subprocess.Popen(['/usr/bin/osascript',tempAppleScriptFileName], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
stdout, stderr = proc.communicate()
print stderr
print stdout
os.unlink(tempAppleScriptFileName)

cmd = 'sleep 1'
print cmd
os.system(cmd)

cmd = 'chmod -Rf go-w /Volumes/"' + title + '"'
print cmd
os.system(cmd)

cmd = 'sync'
print cmd
os.system(cmd)

cmd = 'hdiutil detach ' + device
print cmd
os.system(cmd)

cmd = 'sleep 1'
print cmd
os.system(cmd)

cmd = 'rm -f "' + finalDmgName + '.dmg"'
print cmd
os.system(cmd)

cmd = 'hdiutil convert "%s" -format UDZO -imagekey zlib-level=9 -o "%s.dmg"' % (tempDmgFileName,finalDmgName)
print cmd
os.system(cmd)

cmd = 'rm -f ' + tempDmgFileName
print cmd
os.system(cmd)

cmd = 'ls -lh "%s.dmg"' % (finalDmgName)
print cmd
os.system(cmd)

