import re
import sys
import logging
from apiclient import discovery
import httplib2
from pprint import pprint

# register logger
logging.getLogger("people")

class People:
    def __init__(self, credentials):
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = 'https://people.googleapis.com/$discovery/rest'
        self.service = discovery.build('people', 'v1', http=http,
                                  discoveryServiceUrl=discoveryUrl)
                                  
        self.log = logging.getLogger("people")
        
    def get_email_address(self):
        result = self.service.people().get(
            resourceName="people/me",
            fields="emailAddresses(metadata/source/type,value)"
        ).execute()
        
        for e in result.get('emailAddresses', []):
            if("metadata" not in e): continue
            if("source" not in e["metadata"]): continue
            if("type" not in e["metadata"]["source"]): continue
            if(e["metadata"]["source"]["type"] != "ACCOUNT"): continue
            return(e["value"])
        else:
            return(None)

