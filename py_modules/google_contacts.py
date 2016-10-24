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
        
    #---------------------------------------------------------------------------
    def fetch_groups(self):
        """
        Get all the contact groups in Google Contacts
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
    def fetch_group_entry_by_name(self, group_name):
        feed = self.contacts_client.GetGroups()
        for entry in feed.entry:
            if entry.title.text == group_name:
                return(entry)
                
    #---------------------------------------------------------------------------
    def fetch_people(self, in_Group=None):
        """
        Get all the people in Google Contacts.
        Filter by a specific contacts group using the in_group option
        """
        if(in_Group):
            query = gdata.contacts.client.ContactsQuery()
            if(in_Group.entry is None):
                in_Group.entry = self.fetch_group_entry_by_name(in_Group.name)
            query.group = in_Group.entry.id.text
            feed = self.contacts_client.GetContacts(q=query)
        else:
            feed = self.contacts_client.GetContacts()
            
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
                    
                    for email in entry.email:
                        if email.primary and email.primary == 'true':
                            P.email = email.address
                            break
                    
                    if(len(entry.phone_number) != 0):
                        P.phone = entry.phone_number[0].text
                    
                    for grp in entry.group_membership_info:
                        P._group_hrefs.append(grp.href)
            
            # Traverse to next "page" of feed
            next_link = feed.GetNextLink()
            feed = None
            if(next_link):
                feed = self.gd_client.GetContacts(uri=next_link.href)
        
        return(People)
        
    #---------------------------------------------------------------------------
    def resolve_group_refs(self, People, Groups):
        """
        The People list returned from the fetch_people() method have unresolved
        group membership references.
        If a list of Groups exists, resolve their references
        """
        for P in People:
            P.groups = []
            for href in P._group_hrefs:
                G = contact_defs.get_group_by_id(Groups, href)
                if(G):
                    P.groups.append(G)
            P._group_hrefs = []
        
    #---------------------------------------------------------------------------
    def create_new_group(self, Group):
        """
        Registers a new group with Google Contacts.
        """
        grp = gdata.contacts.data.GroupEntry(title=atom.data.Title(text=Group.name))
        
        entry = self.contacts_client.CreateGroup(grp)
        if(entry is None):
            self.log.error("Unable to create group '%s'" % Group.name)
            sys.exit(1)
        
        Group.entry = entry
        return(Group)

    #---------------------------------------------------------------------------
    def update_contact(self, Person):
        """
        Updates an existing person in Google Contacts.
        """
        if(Person.nickname):
            Person.entry.nickname = gdata.contacts.data.NickName(text=Person.nickname)
        
        if(Person.email):
            Person.entry.email = [gdata.data.Email(
                address=Person.email, 
                primary='true',
                rel=gdata.data.WORK_REL
            )]
        
        if(Person.phone):
            Person.entry.phone_number = [gdata.data.PhoneNumber(
                text=Person.phone,
                primary='true',
                rel=gdata.data.WORK_REL
            )]
        
        Person.entry.group_membership_info = []
        for G in Person.groups:
            membership = gdata.contacts.data.GroupMembershipInfo(href=G.entry.id.text)
            Person.entry.group_membership_info.append(membership)
        
        self.contacts_client.Update(Person.entry)
        
    #---------------------------------------------------------------------------
    def create_new_contact(self, Person):
        """
        Registers a new person with Google Contacts.
        """
        new_contact = gdata.contacts.data.ContactEntry(
            name=gdata.data.Name(
                given_name=gdata.data.GivenName(text=Person.first_name),
                family_name=gdata.data.FamilyName(text=Person.last_name)
            )
        )
        
        if(Person.nickname):
            new_contact.nickname = gdata.contacts.data.NickName(text=Person.nickname)
        
        if(Person.email):
            new_contact.email = [gdata.data.Email(
                address=Person.email, 
                primary='true',
                rel=gdata.data.WORK_REL
            )]
        
        if(Person.phone):
            new_contact.phone_number = [gdata.data.PhoneNumber(
                text=Person.phone,
                primary='true',
                rel=gdata.data.WORK_REL
            )]
        
        new_contact.group_membership_info = []
        for G in Person.groups:
            membership = gdata.contacts.data.GroupMembershipInfo(href=G.entry.id.text)
            new_contact.group_membership_info.append(membership)
        
        entry = self.contacts_client.CreateContact(new_contact)
        Person.entry = entry
        
        if(not entry):
            self.log.error("Upload error when creating contact: %s %s" % (Person.first_name, Person.last_name))
        
    #---------------------------------------------------------------------------
    def delete_contact(self, Person):
        """
        Deletes a person from Google Contacts.
        """
        self.contacts_client.Delete(Person.entry)
        