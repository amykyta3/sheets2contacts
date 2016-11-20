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
                feed = self.contacts_client.GetContacts(uri=next_link.href)
        
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
                feed = self.contacts_client.GetContacts(uri=next_link.href)
        
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

    #---------------------------------------------------------------------------
    def batch_create_groups(self, Groups):
        batches = split_list(Groups, 100)
        for Groups in batches:
            req_feed = gdata.contacts.data.GroupsFeed()
            for i,G in enumerate(Groups):
                grp = gdata.contacts.data.GroupEntry(title=atom.data.Title(text=G.name))
                req_feed.AddInsert(entry=grp, batch_id_string=str(i))
            
            resp_feed = self.contacts_client.ExecuteBatch(req_feed,
                'https://www.google.com/m8/feeds/groups/default/full/batch')
            while(resp_feed):
                if(resp_feed.entry):
                    for entry in resp_feed.entry:
                        idx = int(entry.batch_id.text)
                        Groups[idx].entry = entry
                        
                        self.log.debug('%s: %s (%s)' % (
                            entry.batch_id.text,
                            entry.batch_status.code,
                            entry.batch_status.reason
                        ))
                        
                # Traverse to next "page" of resp_feed
                next_link = resp_feed.GetNextLink()
                resp_feed = None
                if(next_link):
                    resp_feed = self.contacts_client.GetContacts(uri=next_link.href)
        
    #---------------------------------------------------------------------------
    def _update_ContactEntry(self, Person):
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
        
    #---------------------------------------------------------------------------
    def update_contact(self, Person):
        """
        Updates an existing person in Google Contacts.
        """
        self._update_ContactEntry(Person)
        self.contacts_client.Update(Person.entry)
        
    #---------------------------------------------------------------------------
    def _create_ContactEntry(self, Person):
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
        
        return(new_contact)
    #---------------------------------------------------------------------------
    def create_new_contact(self, Person):
        """
        Registers a new person with Google Contacts.
        """
        new_contact = self._create_ContactEntry(Person)
        
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
        
    #---------------------------------------------------------------------------
    def batch_contacts_job(self, create = [], update = [], delete = []):
        
        # Combine all requests into one big list to process.
        # Keep track of what the operation type is with tuple
        requests = []
        for P in create:
            requests.append(("create",P))
        for P in update:
            requests.append(("update",P))
        for P in delete:
            requests.append(("delete",P))
        
        # Process in batches. Google only allows 100 operations per batch
        batches = split_list(requests, 100)
        for request_batch in batches:
            request_feed = gdata.contacts.data.ContactsFeed()
            
            for i,(req_type,P) in enumerate(request_batch):
                if(req_type == "create"):
                    new_c = self._create_ContactEntry(P)
                    request_feed.AddInsert(entry=new_c, batch_id_string=str(i))
                elif(req_type == "update"):
                    self._update_ContactEntry(P)
                    request_feed.AddUpdate(entry=P.entry, batch_id_string=str(i))
                elif(req_type == "delete"):
                    request_feed.AddDelete(entry=P.entry, batch_id_string=str(i))
                    
            # submit the batch request to the server. (use patched method)
            resp_feed = patched_post(self.contacts_client, request_feed,
                'https://www.google.com/m8/feeds/contacts/default/full/batch')
            #resp_feed = self.contacts_client.ExecuteBatch(request_feed,
            #    'https://www.google.com/m8/feeds/contacts/default/full/batch')
            
            while(resp_feed):
                if(resp_feed.entry):
                    for entry in resp_feed.entry:
                        idx = int(entry.batch_id.text)
                        if(request_batch[idx][0] == "create"):
                            request_batch[idx][1].entry = entry
                        
                        self.log.debug('%s: %s (%s)' % (
                            entry.batch_id.text,
                            entry.batch_status.code,
                            entry.batch_status.reason
                        ))

                        
                # Traverse to next "page" of resp_feed
                next_link = resp_feed.GetNextLink()
                resp_feed = None
                if(next_link):
                    resp_feed = self.contacts_client.GetContacts(uri=next_link.href)
        
def split_list(l, n):
    """
    Splits a list into sublists, ensuring each sublist doesn't exceed n items
    For example, input:
        l = [1,2,3,4,5,6,7,8,9,10], n = 3
    output:
        [[1,2,3],[4,5,6],[7,8,9],[10]]
    """
    new_l = []
    while(len(l) > n):
        new_l.append(l[:n])
        l = l[n:]
    if(len(l)): new_l.append(l)
    return(new_l)


def patched_post(client, entry, uri, auth_token=None, converter=None, desired_class=None, **kwargs):
    """
    ExecuteBatch() has a bug when handling Update and Delete jobs.
    This is the workaround function as described here:
    http://stackoverflow.com/questions/23576729/getting-if-match-or-if-none-match-header-or-entry-etag-attribute-required-erro
    
    When it comes time to do a batched delete/updatem instead of calling
    client.ExecuteBatch, instead directly call patched_post:
        patched_post(client_instance, entry_feed,
            'https://www.google.com/m8/feeds/contacts/default/full/batch')
    """
    
    if converter is None and desired_class is None:
        desired_class = entry.__class__
    http_request = atom.http_core.HttpRequest()
    entry_string = entry.to_string(gdata.client.get_xml_version(client.api_version))
    entry_string = entry_string.replace('ns1', 'gd')  # where the magic happens
    http_request.add_body_part(
        entry_string,
        'application/atom+xml')
    return client.request(method='POST', uri=uri, auth_token=auth_token,
                          http_request=http_request, converter=converter,
                          desired_class=desired_class, **kwargs)