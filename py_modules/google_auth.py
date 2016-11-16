
import os
import json
import argparse
import tempfile

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from .google_people import People

CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'sheets2contacts'
SCOPES = " ".join([
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
])

def add_oauth2client_args(parser):
    parser.add_argument('--auth_host_name', default='localhost',
                        help=argparse.SUPPRESS)
    parser.add_argument('--noauth_local_webserver', action='store_true',
                        default=False, help=argparse.SUPPRESS)
    parser.add_argument('--auth_host_port', default=[8080, 8090], type=int,
                        nargs='*', help=argparse.SUPPRESS)
    parser.add_argument(
                        '--logging_level', default='ERROR',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help=argparse.SUPPRESS)
                        
def get_credentials(flags, file_path = None):
    # Setup credentials cache file
    credential_dir = os.path.join(os.path.expanduser('~'), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    if(file_path is None):
        f = tempfile.NamedTemporaryFile(dir=credential_dir, delete=False)
        file_path = f.name
        f.close()
    
    # Try to read cached credentials
    store = Storage(file_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        # Credentials not valid.
        # Complete OAuth2 flow
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        
        P = People(credentials)
        new_credentials_file = "sheets2contacts.%s.json" % P.get_email_address()
        new_credentials_path = os.path.join(credential_dir,new_credentials_file)
        os.rename(file_path, new_credentials_path)
        
    return(credentials)
    

    