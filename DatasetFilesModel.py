#import urllib2
import requests
import HTMLParser
import traceback
from Foundation import NSLog

# The HTML parsing being done here should really be replaced by
# use of the MyTardis RESTful API.  However the RESTful API,
# only seems to have GET methods for retrieving a single record
# - it doesn't seem to have methods like "list all experiment
# IDs I have access to" or "list all data set IDs within this
# experiment."

#https://mytardis.massive.org.au/download/datafile/854/

class DatasetFilesModel:

    def __init__(self,mytardisUrl,username,password,datasetID):
        self.mytardisUrl = mytardisUrl
        self.username = username
        self.password = password
        self.datasetID = datasetID

        self.unhandledExceptionMessage = None

    class MyHtmlParser(HTMLParser.HTMLParser):
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            self.currentDatafileID = None
            self.currentDatafileName = None
            self.datafileIDs = []
            self.datafileUrls = {}
            self.datafileNames = {}
            self.recordingDatafileID = False
            self.recordingDatafileName = False

        def handle_starttag(self, tag, attributes):
            if tag != 'span' and tag != 'a':
                return
            if tag == 'span':
                for name, value in attributes:
                    if name == 'class' and value == 'datafile_name':
                        self.recordingDatafileName = True
            if tag == 'a':
                for name, value in attributes:
                    if name == 'class' and value == 'filelink datafile_name':
                        self.recordingDatafileName = True
            if tag == 'a':
                for name, value in attributes:
                    if name=="id" and value.startswith("datafile_metadata_toggle_"):
                        datafileID = value.split("datafile_metadata_toggle_")[1]
                        self.currentDatafileID = datafileID
                        self.datafileIDs.append(datafileID)
                        self.datafileUrls[datafileID] = "/api/v1/dataset_file/" + datafileID + "/?format=json"
                return       

        def handle_endtag(self, tag):
            if tag == 'span':
                self.recordingDatafileName = False
            if tag == 'a':
                self.recordingDatafileName = False
            if tag == 'tr':
                self.datafileNames[self.currentDatafileID] = self.currentDatafileName
                self.currentDatafileID = None
            return

        def handle_data(self, data):
            if self.recordingDatafileName:
                self.currentDatafileName = data.strip()
            return

    def parseMyTardisDatafileList(self):
        try:
            s = requests.session()
            r = s.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
            if r.status_code==200:
                #NSLog(u"MyTardis authentication succeeded for username: " + unicode(self.username))
                pass
            else:
                #raise Exception("DatasetFilesModel: MyTardis authentication failed for username: " + self.username)
                # Combining Python try/except with Objective-C try/catch is complicated.
                self.unhandledExceptionMessage = "MyTardis authentication failed for username: " + self.username
                return

            #url = self.mytardisUrl + '/dataset/' + self.datasetID
            url = self.mytardisUrl + '/ajax/datafile_list/' + self.datasetID + '/'
            NSLog(u"Until MyTardis's RESTful API has this functionality, we are retrieving the data set's data file IDs from: " + unicode(url))
        
            htmlContent = ""
            r = s.get(url, verify=False)
            for chunk in r.iter_content():
                htmlContent = htmlContent + chunk

            myHtmlParser = self.MyHtmlParser()
            myHtmlParser.feed(htmlContent)
            myHtmlParser.close()

            self.datafileIDs = myHtmlParser.datafileIDs
            self.datafileNames = myHtmlParser.datafileNames
            self.datafileUrls = myHtmlParser.datafileUrls

            #NSLog(unicode(str(self.datafileNames)))

            self.datafiles = {}
            from DatafileModel import DatafileModel
            for datafileID in self.getDatafileIDs():
                datafileName = self.getDatafileNames()[datafileID]
                #NSLog(unicode(datafileName))
                datafile = DatafileModel(self.mytardisUrl,self.username,self.password,datafileID,datafileName)
                self.datafiles[datafileID] = datafile

        except Exception, e:
            NSLog(unicode(traceback.format_exc()))
            self.unhandledExceptionMessage = str(e)

    def getDatafileIDs(self):
        return self.datafileIDs

    def getDatafileNames(self):
        return self.datafileNames

    def getDatafileUrls(self):
        return self.datafileUrls

    def getNumberOfDatafiles(self):
        return len(self.datafileIDs)

    def getDatafiles(self):
        return self.datafiles

    def getUnhandledExceptionMessage(self):
        """
        With PyObjC, you can't rely on the usual Python method of
        raising exceptions, because they might be caught by 
        Objective-C's exception handling mechanism instead of
        Python's.  So whatever method calls parseMyTardisDatafileList
        should check this method afterwards to see if 
        parseMyTardisDatafileList aborted early with an
        exception.
        """
        unhandledExceptionMessage = self.unhandledExceptionMessage
        self.unhandledExceptionMessage = None
        return unhandledExceptionMessage

