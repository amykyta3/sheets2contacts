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
        parser.add_argument('-n --dry-run', dest='dry_run', default=False,
                            action="store_true",
                            help='Google Sheet ID or URL')
        
        g_auth.add_oauth2client_args(parser)
        
    def main(self):
        App.main(self)
        
        logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)
        
        # If no sheet specified, ask
        if(self.options.sheet_id == None):
            print("Enter the Google Sheets URL to sync from:")
            self.options.sheet_id = raw_input('> ')
        
        # Sanitize sheet ID URL
        m = re.search(r'docs.google.com\/spreadsheets\/d\/([^\/]+)\/', self.options.sheet_id)
        if(m):
            # --sheet option is a URL. Extract
            self.options.sheet_id = m.group(1)
        
        credentials = g_auth.get_credentials(self.options)
        
        #-----------------------------------------------------------------------
        # Fetch contact data from Google Sheets spreadsheet
        #-----------------------------------------------------------------------
        S = Sheets(credentials, self.options.sheet_id)
        sGroups, sPeople = S.fetch_sheet_data()
        
        #-----------------------------------------------------------------------
        # Fetch contact data from Google Contacts (only ones in sheets2contacts group)
        #-----------------------------------------------------------------------
        C = Contacts(credentials)
        cGroups = C.fetch_groups()
        sheets2contacts_group = cd.get_group_by_name(cGroups, "Synced with sheets2contacts")
        if(sheets2contacts_group == None):
            # "sheets2contacts" group doesn't exist. Create it
            cPeople = []
            sheets2contacts_group = cd.Group("Synced with sheets2contacts")
            if(self.options.dry_run):
                self.log.info("Would create new contacts group: 'Synced with sheets2contacts'")
            else:
                self.log.info("Creating new contacts group: 'Synced with sheets2contacts'")
                C.create_new_group(sheets2contacts_group)
            cGroups.append(sheets2contacts_group)
        else:
            cPeople = C.fetch_people(in_Group=sheets2contacts_group)
            C.resolve_group_refs(cPeople, cGroups)
        
        #-----------------------------------------------------------------------
        # Create new contact groups if necessary
        #-----------------------------------------------------------------------
        new_groups = []
        for sG in sGroups:
            for cG in cGroups:
                if(sG.name == cG.name):
                    break
            else:
                # Group was not found. Create a new one
                if(self.options.dry_run):
                    self.log.info("Would create new contacts group: '%s'" % sG.name)
                else:
                    self.log.info("Creating new contacts group: '%s'" % sG.name)
                    C.create_new_group(sG)
                new_groups.append(sG)
        cGroups.extend(new_groups)
        
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
        while(len(sPeople)):
            P = sPeople.pop()
            for cP in cPeople:
                if((P.first_name == cP.first_name) and (P.last_name == cP.last_name)):
                    # Found match! Update
                    changed = cP.update(P)
                    if(changed):
                        # transmit updated person to the google
                        if(self.options.dry_run):
                            self.log.info("Would update contact: '%s %s'" % (cP.first_name, cP.last_name))
                        else:
                            self.log.info("Updating contact: '%s %s'" % (cP.first_name, cP.last_name))
                            C.update_contact(cP)
                    
                    # Contact was handled. remove
                    cPeople.remove(cP)
                    break
            else:
                # Person not found in existing contacts.
                # Create new and transmit new person to the google
                if(self.options.dry_run):
                    self.log.info("Would create contact: '%s %s'" % (P.first_name, P.last_name))
                else:
                    self.log.info("Creating contact: '%s %s'" % (P.first_name, P.last_name))
                    C.create_new_contact(P)
        
        #-----------------------------------------------------------------------
        # Any contacts left over in cPeople are ones that were not in the sheet
        # Delete them
        #-----------------------------------------------------------------------
        for cP in cPeople:
            # Delete contact from the google
            if(self.options.dry_run):
                self.log.info("Would delete contact: '%s %s'" % (cP.first_name, cP.last_name))
            else:
                self.log.info("Deleting contact: '%s %s'" % (cP.first_name, cP.last_name))
                C.delete_contact(cP)
    
################################################################################
if __name__ == '__main__':
    A = sheets2contacts()
    A.main()