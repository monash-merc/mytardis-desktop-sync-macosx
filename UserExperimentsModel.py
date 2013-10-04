import requests
import HTMLParser
import traceback
from Foundation import NSLog

class UserExperimentsModel:

    def __init__(self,mytardisUrl,username,password):
        self.mytardisUrl = mytardisUrl
        self.username = username
        self.password = password

        self.unhandledExceptionMessage = None

    # The HTML parsing being done here should really be replaced by
    # use of the MyTardis RESTful API.  However the RESTful API,
    # only seems to have GET methods for retrieving a single record
    # - it doesn't seem to have methods like "list all experiment
    # IDs I have access to" or "list all data set IDs within this
    # experiment."

    class MyTardisExperimentsHtmlParser(HTMLParser.HTMLParser):
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            self.currentExperimentID = None
            self.experimentIDs = []
            self.experimentUrls = {}
            self.experimentTitles = {}
            self.recordingExperimentTitle = False

        def handle_starttag(self, tag, attributes):
            if tag != 'div' and tag !='a':
                return
            if tag == 'div':
                for name, value in attributes:
                    if name == 'about' and value.startswith('/experiment/view/'):
                        experimentID = value.split('/experiment/view/')[1]
                        experimentID = experimentID.strip("/")
                        self.currentExperimentID = experimentID
                        self.experimentIDs.append(experimentID)
                        self.experimentUrls[experimentID] = value
                        break
                return       
            if tag == 'a':
                for name, value in attributes:
                    if name == 'href' and self.currentExperimentID is not None and value==self.experimentUrls[self.currentExperimentID]:
                        self.recordingExperimentTitle = True
                        break
                return       

        def handle_endtag(self, tag):
            if tag == 'a':
                self.recordingExperimentTitle = False
            return

        def handle_data(self, data):
            if self.recordingExperimentTitle:
                self.experimentTitles[self.currentExperimentID] = data.strip()
            return

    def parseMyTardisExperimentList(self):
        try:
            s = requests.session()
            r = s.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
            if r.status_code==200:
                #NSLog(u"MyTardis authentication succeeded for username: " + self.username)
                pass
            else:
                # raise Exception("MyTardis authentication failed for username: " + self.username)
                # Combining Python try/except with Objective-C try/catch is complicated.
                self.unhandledExceptionMessage = "MyTardis authentication failed for username: " + self.username
                return

            experimentsUrl = self.mytardisUrl + '/experiment/list/mine'
            NSLog(u"Until MyTardis's RESTful API has this functionality, we are retrieving the user's experiment IDs from: " + unicode(experimentsUrl))

            htmlContent = ""
            r = s.get(experimentsUrl, verify=False)
            for chunk in r.iter_content():
                htmlContent = htmlContent + chunk

            mytardisExperimentsHtmlParser = self.MyTardisExperimentsHtmlParser()
            mytardisExperimentsHtmlParser.feed(htmlContent)
            mytardisExperimentsHtmlParser.close()

            self.experimentIDs = mytardisExperimentsHtmlParser.experimentIDs
            self.experimentTitles = mytardisExperimentsHtmlParser.experimentTitles
            self.experimentUrls = mytardisExperimentsHtmlParser.experimentUrls

            # We can get more info on an experiment from the URL: /api/v1/experiment/<experiment_id>/?format=json

            self.experiments = {}
            from ExperimentModel import ExperimentModel
            for experimentID in self.getExperimentIDs():
                experimentTitle = self.getExperimentTitles()[experimentID]
                experiment = ExperimentModel(self.mytardisUrl,self.username,self.password,experimentID,experimentTitle)
                self.experiments[experimentID] = experiment

        except Exception, e:
            NSLog(unicode(traceback.format_exc()))
            self.unhandledExceptionMessage = str(e)

    def getExperimentIDs(self):
        return self.experimentIDs

    def getExperimentTitles(self):
        return self.experimentTitles

    def getExperimentUrls(self):
        return self.experimentUrls

    def getNumberOfExperiments(self):
        return len(self.experimentIDs)

    def getExperiments(self):
        return self.experiments

    def getExperiment(self,experimentID):
        return self.experiments[experimentID]

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

