
import gdata.contacts.client

class Contacts:
    def __init__(self, credentials):
        auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
        self.contacts_client = gdata.contacts.client.ContactsClient()
        self.contacts_client = auth2token.authorize(self.contacts_client)
