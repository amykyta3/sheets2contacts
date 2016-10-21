
import re
import sys
import logging
from apiclient import discovery
import httplib2
from . import contact_defs

# register logger
logging.getLogger("sheets")

class Sheets:
    def __init__(self, credentials, sheet_id):
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.sheets_service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)
                                  
        self.sheet_id = sheet_id
        self.log = logging.getLogger("sheets")
        
    #---------------------------------------------------------------------------
    def fetch_sheet_data(self):
        self.log.info("Fetching contact info from Google Sheets spreadsheet...")
        column_map = self.get_column_map()
        column_data = self.get_column_data(column_map)
        Groups, People = self.elaborate_column_data(column_data)
        self.log.info("Found %d contacts in %d groups" % (len(People), len(Groups)))
        return(Groups, People)
    #---------------------------------------------------------------------------
    def get_column_map(self):
        """
        Lookup the Google Sheet's mapping tab and fetch the settings
        """
        valid_keys = [
            "sheet",
            "first_name",
            "last_name",
            "nickname",
            "email",
            "phone",
            "groups"
        ]
        
        rangeName = 'sheets2contacts!A2:B'
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=rangeName).execute()
        values = result.get('values', [])
        
        # convert to dict
        kv_dict = {}
        for row in values:
            kv_dict[row[0].strip()] = row[1].strip()
        
        # Sanitize dict to only contain valid keys
        bad_keys = set(kv_dict) - set(valid_keys)
        for bad_key in bad_keys:
            self.log.warning("Ignoring key: %s" % bad_key)
            del(kv_dict[bad_key])
        
        # Extract sheet name from dict
        if("sheet" not in kv_dict):
            self.log.error("sheet2contacts tab is missing required key: sheet")
            sys.exit(1)
        sheet_name = kv_dict['sheet']
        del(kv_dict['sheet'])
        self.log.debug("Got sheet name: %s" % sheet_name)
        
        # Fetch sheet headings
        rangeName = sheet_name + "!1:1"
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=rangeName).execute()
        headings = result.get('values', [])[0]
        
        # Resolve headings in kv_dict
        self.log.debug("Resolving column mappings...")
        for k,v in kv_dict.items():
            if(v not in headings):
                self.log.error("Heading '%s' not found for key: %s" % (v, k))
                sys.exit(1)
            column = idx2col(headings.index(v))
            kv_dict[k] = "%s!%s2:%s" % (sheet_name, column, column)
            self.log.debug("  %s: %s --> %s" % (k,v,kv_dict[k]))
        
        return(kv_dict)
        
    #---------------------------------------------------------------------------
    def get_column_data(self, column_map):
        """
        Fetches the columns specified in the column map
        """
        
        # prepare ranges. Need to fetch and receive in a known order
        keys = []
        ranges = []
        for k,v in column_map.items():
            keys.append(k)
            ranges.append(v)
        
        ranges = column_map.values()
        result = self.sheets_service.spreadsheets().values().batchGet(
            spreadsheetId=self.sheet_id,
            ranges=ranges,
            majorDimension="COLUMNS",
            fields="valueRanges/values"
        ).execute()
        valueRanges = result.get('valueRanges', [])
        
        column_data = {}
        for i, key in enumerate(keys):
            v = valueRanges[i].get('values', [[]])
            column_data[key] = v[0]
        
        return(column_data)
    
    #---------------------------------------------------------------------------
    def elaborate_column_data(self, column_data):
        """
        converts the column_data into Person and Group lists
        """
        
        Groups = []
        People = []
        
        # Collect all the groups that exist
        group_names = set()
        group_rows = column_data.get('groups', [])
        for row in group_rows:
            group_names |= set(re.split(r'[,;]', row))
        
        # Convert groups into Group objects
        # also store into a dict for convenience
        groups_dict = {}
        for group_name in group_names:
            group_name = group_name.strip()
            G = contact_defs.Group(group_name)
            Groups.append(G)
            groups_dict[group_name] = G
        self.log.debug("Received %d unique groups" % len(Groups))
            
        # Determine number of people (the largest dimension in the table)
        n_people = 0
        for v in column_data.values():
            n_people = max(n_people, len(v))
        self.log.debug("Received %d contact entries" % n_people)
        
        # Convert column_data into People objects
        for i in range(n_people):
            P = contact_defs.Person()
            P.first_name = self.get_cell(column_data, "first_name",i)
            P.last_name = self.get_cell(column_data, "last_name",i)
            P.nickname = self.get_cell(column_data, "nickname",i)
            P.email = self.get_cell(column_data, "email",i)
            P.phone = self.get_cell(column_data, "phone",i)
            
            # Determine group membership
            groups_str = self.get_cell(column_data, "groups",i)
            if(groups_str != None):
                group_names = set(re.split(r'[,;]', groups_str))
                for group_name in group_names:
                    group_name = group_name.strip()
                    P.groups.append(groups_dict[group_name])
            
            People.append(P)
        return(Groups, People)
            
    def get_cell(self, column_data, col, idx, default=None):
        """
        Fetch a single cell from column_data
        """
        column = column_data.get(col, [])
        if(idx >= len(column)):
            return(default)
        else:
            return(column[idx])
    
    
def idx2col(idx):
    """
    Convert an index to a column heading code
    0 --> A
    1 --> B
    25 --> Z
    26 --> AA
    """
    s = chr(ord('A') + (idx % 26))
    if(idx >= 26):
        s = idx2col(idx//26 - 1) + s
    return(s)