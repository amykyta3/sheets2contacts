
import os

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'sheets2contacts'
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly https://www.googleapis.com/auth/contacts'

def add_oauth2client_args(parser):
    oa_group = parser.add_argument_group("oauth2client", "oauth2client options")
    oa_group.add_argument('--auth_host_name', default='localhost',
                        help='Hostname when running a local web server.')
    oa_group.add_argument('--noauth_local_webserver', action='store_true',
                        default=False, help='Do not run a local web server.')
    oa_group.add_argument('--auth_host_port', default=[8080, 8090], type=int,
                        nargs='*', help='Port web server should listen on.')
    oa_group.add_argument(
                        '--logging_level', default='ERROR',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level of detail.')
                        
def get_credentials(flags):
    # Setup credentials cache file
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'sheets2contacts.json')
    
    # Try to read cached credentials
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        # Credentials not valid.
        # Complete OAuth2 flow
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    
    return(credentials)
    