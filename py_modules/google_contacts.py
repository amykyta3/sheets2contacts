import sys
import logging

import atom
import gdata.contacts.client
from pprint import pprint

from . import contact_defs

# register logger
logging.getLogger("contacts")

class Contacts:
    def __init__(self, credentials):
        
        auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
        self.contacts_client = gdata.contacts.client.ContactsClient()
        self.contacts_client = auth2token.authorize(self.contacts_client)
        
        self.log = logging.getLogger("contacts")
        
        self.Groups = self.fetch_groups()
        self.People = self.fetch_people()
        
    #---------------------------------------------------------------------------
    def fetch_groups(self):
        """
        Get all the contact groups
        """
        Groups = []
        
        feed = self.contacts_client.GetGroups()
        while(feed):
            if(feed.entry):
                for entry in feed.entry:
                    G = contact_defs.Group(entry.title.text)
                    G.entry = entry
                    Groups.append(G)
            
            # Traverse to next "page" of feed
            next_link = feed.GetNextLink()
            feed = None
            if(next_link):
                feed = self.gd_client.GetContacts(uri=next_link.href)
        
        return(Groups)
    
    #---------------------------------------------------------------------------
    def fetch_people(self):
        """
        Fetch all the contacts that are managed by sheets2contacts
        These contacts are the ones in the group named "sheets2contacts"
        """
        
        grp = self.get_group_by_name("sheets2contacts")
        if(grp is None):
            self.log.info("Did not find group 'sheets2contacts'. No exitsting contacts to sync against")
            return([])
        
        query = gdata.contacts.client.ContactsQuery()
        query.group = grp.entry.id.text
        feed = self.contacts_client.GetContacts(q=query)
        People = []
        while(feed):
            if(feed.entry):
                for entry in feed.entry:
                    P = contact_defs.Person()
                    P.entry = entry
                    People.append(P)
                    
                    if(entry.name is not None):
                        if(entry.name.family_name):
                            P.last_name = entry.name.family_name.text
                        if(entry.name.given_name):
                            P.first_name = entry.name.given_name.text
                    else:
                        P.first_name = entry.title.text
                    
                    if(entry.nickname is not None):
                        P.nickname = entry.nickname.text
                    
                    if(len(entry.email) != 0):
                        P.email = entry.email[0].text
                    
                    if(len(entry.phone_number) != 0):
                        P.phone = entry.phone_number[0].text
                    
                    for grp in entry.group_membership_info:
                        G = self.get_group_by_id(grp.href)
                        P.groups.append(G)
            
            # Traverse to next "page" of feed
            next_link = feed.GetNextLink()
            feed = None
            if(next_link):
                feed = self.gd_client.GetContacts(uri=next_link.href)
        
        return(People)
        
    #---------------------------------------------------------------------------
    def get_group_by_name(self, group_name):
        """
        Lookup a group by name
        """
        for G in self.Groups:
            if(G.name == group_name):
                return(G)
        return(None)
    
    #---------------------------------------------------------------------------
    def get_group_by_id(self, gid):
        """
        Lookup a group by ID
        """
        for G in self.Groups:
            if(G.entry.id.text == gid):
                return(G)
        return(None)
        
    #---------------------------------------------------------------------------
    def create_new_group(self, group_name):
        grp = gdata.contacts.data.GroupEntry(title=atom.data.Title(text=group_name))
        
        entry = self.contacts_client.CreateGroup(grp)
        if(entry is None):
            self.log.error("Unable to create group '%s'" % group_name)
            sys.exit(1)
            
        G = contact_defs.Group(group_name)
        G.entry = entry
        return(G)
        