import requests
import traceback
import unicodedata
import re
from Foundation import NSLog

class DatasetModel:

    def __init__(self,mytardisUrl,username,password,datasetID,datasetTitle):
        self.mytardisUrl = mytardisUrl
        self.username = username
        self.password = password
        self.datasetID = datasetID
        self.datasetTitle = datasetTitle

    def getJson(self):
        try:
            s = requests.session()
            r = s.post(self.mytardisUrl + '/login/', {'username':self.username,'password':self.password}, verify=False)
            if r.status_code==200:
                NSLog(u"MyTardis authentication succeeded for username: " + unicode(self.username))
            else:
                raise Exception("MyTardis authentication failed for username: " + self.username)

            datasetUrl = self.mytardisUrl + '/api/v1/dataset/'+datasetID+'/?format=json'

            r = s.get(datasetUrl, verify=False)
            self.json = r.json()

        except:
            NSLog(unicode(traceback.format_exc()))

        return self.json

    def getDirectoryName(self):
        if hasattr(self,'json') and self.json is not None:
            return str(self.json['id']) + " - " + slugify(self.json['title'])
        else:
            return str(self.datasetID) + " - " + slugify(self.datasetTitle.decode("unicode-escape"))

def slugify(value):
    """
    Normalizes string, and removes non-alpha characters.
    This ensures that we can create a legal folder name 
    from the dataset name.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    #value = unicode(re.sub('[-\s]+', '-', value))
    return value
    

