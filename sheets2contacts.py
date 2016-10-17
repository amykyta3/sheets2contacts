#!/usr/bin/env python

import os
import sys

from py_modules.app import App
import py_modules.google_auth as g_auth
from py_modules.google_contacts import Contacts
from py_modules.google_sheets import Sheets

class sheets2contacts(App):
    def set_cmdline_args(self, parser):
        App.set_cmdline_args(self, parser)
        parser.description = "Synchronize Gmail contacts with a Google Sheet"
        
        parser.add_argument('--sheet', dest='sheet_id', default=None,
                            help='Google Sheet ID or URL')
        
        g_auth.add_oauth2client_args(parser)
        
    def main(self):
        App.main(self)
        
        
        credentials = g_auth.get_credentials(self.options)
        S = Sheets(credentials, self.options.sheet_id)
        C = Contacts(credentials)
        
        print("Printing people!")
        for P in S.People:
            print(P.first_name, P.last_name)
        
        """
        Program flow:
            Fetch key from Sheet
                In sheets2contacts tab of sheet.
                This defines which items get synced, and how they link to sheet
                columns.
            Fetch all contacts from sheet
                Using key, Generate a list of ContactCard objects
                Anything not specified in key gets None
                
            Fetch all existing contacts from Contacts
                Convert each contact's data to a ContactCard
                Keep handle to contact's ID in ContactCard
            
            Fetch all existing Groups from Contacts
            
            Sync Groups
                If sheet's group does not exist, create it
                Leave extra groups in Contacts unused
                contacts will get unlinked from groups they do not belong to.
            
            Sync contacts
                Contact's primary key is firstname/lastname.
                Pair up and compare to create the following lists to act on:
                    new:
                        These are contacts that exist in the sheet, but not in Contacts
                        Add them
                        
                    update:
                        Match found. Update the existing Contacts entry
                        Only update items that are listed in sheet's key
                        Only update items that changed
                        
                    delete:
                        Contact not found in Sheet
                        Delete from Contacts?
                        At the very least, unlink from any groups.
                        Possibly assign to a "trash" group. Leave it up to to
                        the user to clean-up
        """
        
################################################################################
if __name__ == '__main__':
    A = sheets2contacts()
    A.main()