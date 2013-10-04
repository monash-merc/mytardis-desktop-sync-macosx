import requests
import traceback
import unicodedata
import re
from Foundation import NSLog

class ExperimentModel:

    def __init__(self,mytardisUrl,username,password,experimentID,experimentTitle):
        self.mytardisUrl = mytardisUrl
        self.username = username
        self.password = password
        self.experimentID = experimentID
        self.experimentTitle = experimentTitle
        self.optIn = False

    def getJson(self):
        try:
            s = requests.session()
            r = s.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
            if r.status_code==200:
                NSLog(u"MyTardis authentication succeeded for username: " + unicode(self.username))
            else:
                raise Exception("MyTardis authentication failed for username: " + self.username)

            experimentUrl = self.mytardisUrl + '/api/v1/experiment/'+experimentID+'/?format=json'

            r = s.get(experimentUrl, verify=False)
            self.json = r.json()

        except:
            NSLog(unicode(traceback.format_exc()))

        return self.json

    def getDirectoryName(self):
        if hasattr(self,'json') and self.json is not None:
            return str(self.json['id']) + " - " + slugify(self.json['title'])
        else:
            return str(self.experimentID) + " - " + slugify(self.experimentTitle.decode("unicode-escape"))

    def setOptIn(self,optIn):
        self.optIn = optIn
        if self.optIn==1 or self.optIn=="1":
            self.optIn = True
        if self.optIn==0 or self.optIn=="0":
            self.optIn = False

    def getOptIn(self):
        return self.optIn

def slugify(value):
    """
    Normalizes string, and removes non-alpha characters.
    This ensures that we can create a
    legal directory name from the experiment name.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    return value
    

