import requests
import HTMLParser
import traceback
from Foundation import NSLog

class ExperimentDatasetsModel:

    def __init__(self,mytardisUrl,username,password,experimentID):
        self.mytardisUrl = mytardisUrl
        self.username = username
        self.password = password
        self.experimentID = experimentID

        self.unhandledExceptionMessage = None

    # The HTML parsing being done here should really be replaced by
    # use of the MyTardis RESTful API.  However the RESTful API,
    # only seems to have GET methods for retrieving a single record
    # - it doesn't seem to have methods like "list all experiment
    # IDs I have access to" or "list all data set IDs within this
    # experiment."

    class MyHtmlParser(HTMLParser.HTMLParser):
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            self.currentDatasetID = None
            self.datasetIDs = []
            self.datasetUrls = {}
            self.datasetTitles = {}
            self.recordingDatasetTitle = False

        def handle_starttag(self, tag, attributes):
            if tag !='a':
                return
            if tag == 'a':
                for name, value in attributes:
                    if name == 'href' and value.startswith("/dataset/"):
                        datasetID = value.split('/dataset/')[1]
                        self.currentDatasetID = datasetID
                        self.datasetIDs.append(datasetID)
                        self.recordingDatasetTitle = True
                        self.datasetUrls[datasetID] = value
                        break
                return       

        def handle_endtag(self, tag):
            if tag == 'a':
                self.recordingDatasetTitle = False
            return

        def handle_data(self, data):
            if self.recordingDatasetTitle:
                self.datasetTitles[self.currentDatasetID] = data.strip()
            return

    def parseMyTardisDatasetList(self):
        try:
            s = requests.session()
            r = s.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
            if r.status_code==200:
                #NSLog(u"MyTardis authentication succeeded for username: " + self.username)
                pass
            else:
                #raise Exception("ExperimentDatasetsModel: MyTardis authentication failed for username: " + self.username)
                # Combining Python try/except with Objective-C try/catch is complicated.
                self.unhandledExceptionMessage = "MyTardis authentication failed for username: " + self.username
                return

            url = self.mytardisUrl + '/experiment/view/' + self.experimentID + '/'
            NSLog(u"Until MyTardis's RESTful API has this functionality, we are retrieving the experiment's data set IDs from: " + unicode(url))

            htmlContent = ""
            r = s.get(url, verify=False)
            for chunk in r.iter_content():
                htmlContent = htmlContent + chunk

            myHtmlParser = self.MyHtmlParser()
            myHtmlParser.feed(htmlContent)
            myHtmlParser.close()

            self.datasetIDs = myHtmlParser.datasetIDs
            self.datasetTitles = myHtmlParser.datasetTitles
            self.datasetUrls = myHtmlParser.datasetUrls

            self.datasets = {}
            from DatasetModel import DatasetModel
            for datasetID in self.getDatasetIDs():
                datasetTitle = self.getDatasetTitles()[datasetID]
                dataset = DatasetModel(self.mytardisUrl,self.username,self.password,datasetID,datasetTitle)
                self.datasets[datasetID] = dataset

        except Exception, e:
            NSLog(unicode(traceback.format_exc()))
            self.unhandledExceptionMessage = str(e)

    def getDatasetIDs(self):
        return self.datasetIDs

    def getDatasetTitles(self):
        return self.datasetTitles

    def getDatasetUrls(self):
        return self.datasetUrls

    def getNumberOfDatasets(self):
        return len(self.datasetIDs)

    def getDatasets(self):
        return self.datasets

    def getUnhandledExceptionMessage(self):
        """
        With PyObjC, you can't rely on the usual Python method of
        raising exceptions, because they might be caught by 
        Objective-C's exception handling mechanism instead of
        Python's.  So whatever method calls parseMyTardisDatasetList
        should check this method afterwards to see if 
        parseMyTardisDatasetList aborted early with an
        exception.
        """
        unhandledExceptionMessage = self.unhandledExceptionMessage
        self.unhandledExceptionMessage = None
        return unhandledExceptionMessage

