#!/usr/bin/env python

import re
import os
import sys
import logging

from py_modules.app import App
import py_modules.google_auth as g_auth
from py_modules.google_contacts import Contacts
from py_modules.google_sheets import Sheets
import py_modules.contact_defs as cd

class sheets2contacts(App):
    def set_cmdline_args(self, parser):
        App.set_cmdline_args(self, parser)
        parser.description = "Synchronize Gmail contacts with a Google Sheet"
        
        parser.add_argument('--sheet', dest='sheet_id', default=None,
                            help='Google Sheet ID or URL')
        parser.add_argument('--email', dest='email', default=None,
                            help='Email of existing stored credentials to sync to')
        parser.add_argument('-n --dry-run', dest='dry_run', default=False,
                            action="store_true",
                            help='Google Sheet ID or URL')
        
        g_auth.add_oauth2client_args(parser)
        
    def main(self):
        App.main(self)
        
        logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)
        
        #-----------------------------------------------------------------------
        # Determine which sheet to sync to
        #-----------------------------------------------------------------------
        # If no sheet specified, ask
        if(self.options.sheet_id == None):
            print("Enter the Google Sheets URL to sync from:")
            self.options.sheet_id = raw_input('> ')
        
        # Sanitize sheet ID URL
        m = re.search(r'docs.google.com\/spreadsheets\/d\/([^\/]+)\/', self.options.sheet_id)
        if(m):
            # --sheet option is a URL. Extract
            self.options.sheet_id = m.group(1)
        
        #-----------------------------------------------------------------------
        # Determine which credentials to use
        #-----------------------------------------------------------------------
        credential_dir = os.path.join(os.path.expanduser('~'), '.credentials')
        
        if(self.options.email == None):
            emails = []
            for f in os.listdir(credential_dir):
                m = re.search(r'sheets2contacts\.(.+)\.json', f)
                if(m): emails.append(m.group(1))
            
            if(len(emails)):
                print("Choose which email account to sync to:")
                for i,e in enumerate(emails):
                    print("  %d: %s" % (i+1,e))
                print("  0: Authenticate New")
                sel = int(raw_input('> '))
                if(sel > 0 and sel <= len(emails)):
                    self.options.email = emails[sel-1]
        
        if(self.options.email == None):
            credential_file = None
        else:
            credential_file = os.path.join(credential_dir, "sheets2contacts.%s.json" % self.options.email)
            if(not os.path.exists(credential_file)): credential_file = None
        
        credentials = g_auth.get_credentials(self.options, credential_file)
        
        #-----------------------------------------------------------------------
        # Fetch contact data from Google Sheets spreadsheet
        #-----------------------------------------------------------------------
        self.log.info("Fetching contact info from Google Sheets spreadsheet...")
        S = Sheets(credentials, self.options.sheet_id)
        sGroups, sPeople = S.fetch_sheet_data()
        self.log.info("Found %d contacts and %d groups" % (len(sPeople), len(sGroups)))
        
        #-----------------------------------------------------------------------
        # Fetch contact data from Google Contacts (only ones in sheets2contacts group)
        #-----------------------------------------------------------------------
        self.log.info("Fetching existing synced contacts from Google Contacts...")
        groups_to_create = []
        C = Contacts(credentials)
        cGroups = C.fetch_groups()
        sheets2contacts_group = cd.get_group_by_name(cGroups, "Synced with sheets2contacts")
        if(sheets2contacts_group == None):
            # "sheets2contacts" group doesn't exist. Create it
            cPeople = []
            sheets2contacts_group = cd.Group("Synced with sheets2contacts")
            groups_to_create.append(sheets2contacts_group)
            cGroups.append(sheets2contacts_group)
        else:
            cPeople = C.fetch_people(in_Group=sheets2contacts_group)
            C.resolve_group_refs(cPeople, cGroups)
        self.log.info("Found %d contacts and %d groups" % (len(cPeople), len(cGroups)))
        #-----------------------------------------------------------------------
        # Determine which groups need to be created
        #-----------------------------------------------------------------------
        new_groups = []
        for sG in sGroups:
            for cG in cGroups:
                if(sG.name == cG.name):
                    break
            else:
                # Group was not found. Create a new one
                self.log.debug("Need to create group: '%s'" % sG.name)
                new_groups.append(sG)
        
        cGroups.extend(new_groups)
        groups_to_create.extend(new_groups)
        
        #-----------------------------------------------------------------------
        # Submit new groups to Google
        #-----------------------------------------------------------------------
        if(self.options.dry_run):
            self.log.info("Would create %d new groups..." % len(groups_to_create))
        else:
            self.log.info("Creating %d new groups..." % len(groups_to_create))
            C.batch_create_groups(groups_to_create)
        
        for G in groups_to_create:
            self.log.debug("  %s" % G.name)
        
        #-----------------------------------------------------------------------
        # Update group references for people from sheets to use actuals
        # All people to be synced also need to be in the "sheets2contacts" group
        #  as well as the builtin "My Contacts" group
        #-----------------------------------------------------------------------
        my_contacts_group = cd.get_group_by_name(cGroups, "System Group: My Contacts")
        for P in sPeople:
            new_groups = [my_contacts_group, sheets2contacts_group]
            for G in P.groups:
                new_G = cd.get_group_by_name(cGroups, G.name)
                if(new_G == None):
                    self.log.error("Something went wrong. Group should exist")
                    sys.exit(1)
                new_groups.append(new_G)
            P.groups = new_groups
        
        
        #-----------------------------------------------------------------------
        # Update contacts as necessary
        #-----------------------------------------------------------------------
        contacts_to_update = []
        contacts_to_create = []
        
        while(len(sPeople)):
            P = sPeople.pop()
            for cP in cPeople:
                if((P.first_name == cP.first_name) and (P.last_name == cP.last_name)):
                    # Found match! Update
                    changed = cP.update(P)
                    if(changed):
                        self.log.debug("Need to update: '%s %s'" % (cP.first_name, cP.last_name))
                        contacts_to_update.append(cP)
                        
                    
                    # Contact was handled. remove
                    cPeople.remove(cP)
                    break
            else:
                # Person not found in existing contacts.
                self.log.debug("Need to create: '%s %s'" % (P.first_name, P.last_name))
                contacts_to_create.append(P)
                
        
        #-----------------------------------------------------------------------
        # Any contacts left over in cPeople are ones that were not in the sheet
        # Delete them
        #-----------------------------------------------------------------------
        contacts_to_delete = cPeople
        
        for PD in contacts_to_delete:
            self.log.debug("Need to delete: '%s %s'" % (PD.first_name, PD.last_name))
        
        #-----------------------------------------------------------------------
        # Submit updates to Google
        #-----------------------------------------------------------------------
        if(self.options.dry_run):
            self.log.info("Would create %d, update %d, delete %d contacts ..." % (
                len(contacts_to_create), len(contacts_to_update), len(contacts_to_delete)
            ))
        else:
            self.log.info("Creating %d, updating %d, deleting %d contacts ..." % (
                len(contacts_to_create), len(contacts_to_update), len(contacts_to_delete)
            ))
            
            C.batch_contacts_job(
                create=contacts_to_create,
                update=contacts_to_update,
                delete=contacts_to_delete
            )
        
        
################################################################################
if __name__ == '__main__':
    A = sheets2contacts()
    A.main()