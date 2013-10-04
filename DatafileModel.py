import requests
import traceback
import unicodedata
import re
from Foundation import NSLog

class DatafileModel:

    def __init__(self,mytardisUrl,username,password,datafileID,datafileName):
        self.mytardisUrl = mytardisUrl
        self.username = username
        self.password = password
        self.datafileID = datafileID
        self.datafileName = datafileName
        self.unhandledExceptionMessage = None

    def getJson(self):
        try:
            s = requests.session()
            r = s.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
            if r.status_code==200:
                NSLog(u"MyTardis authentication succeeded for username: " + unicode(self.username))
            else:
                raise Exception("MyTardis authentication failed for username: " + self.username)

            datafileUrl = self.mytardisUrl + '/api/v1/dataset_file/'+datafileID+'/?format=json'

            r = s.get(datafileUrl, verify=False)
            self.json = r.json()

        except Exception, e:
            NSLog(unicode(traceback.format_exc()))
            self.unhandledExceptionMessage = str(e)

        return self.json

    def getFileName(self):
        return self.datafileName

    def getDownloadUrl(self):
        return self.mytardisUrl + "/download/datafile/" + self.datafileID + "/"

    def downloadTo(self,pathToDownloadTo,session):
        NSLog(u"datafile.downloadTo")
        NSLog(u"datafileID = " + unicode(str(self.datafileID)))
        NSLog(u"datafile.getFileName() = " + unicode(self.getFileName()))
        try:
            NSLog(u"Downloading " + self.getFileName() + " from " + self.getDownloadUrl())

            r = session.get(self.getDownloadUrl(), verify=False)
            with open(pathToDownloadTo, 'wb') as f:
                for chunk in r.iter_content(chunk_size=512 * 1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
        except Exception, e:
            NSLog(unicode(traceback.format_exc()))
            self.unhandledExceptionMessage = str(e)

    def getUnhandledExceptionMessage(self):
        """
        With PyObjC, you can't rely on the usual Python method of
        raising exceptions, because they might be caught by 
        Objective-C's exception handling mechanism instead of
        Python's.  So whatever method calls parseMyTardisExperimentList
        should check this method afterwards to see if 
        parseMyTardisExperimentList aborted early with an
        exception.
        """
        unhandledExceptionMessage = self.unhandledExceptionMessage
        self.unhandledExceptionMessage = None
        return unhandledExceptionMessage

