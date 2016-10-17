
from apiclient import discovery
import httplib2

class Sheets:
    def __init__(self, credentials, sheet_id):
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.sheets_service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)
                                  
        self.sheet_id = sheet_id
        
    def test(self):
        rangeName = 'sheets2contacts!A2:B'
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            print('Key, Value:')
            for row in values:
                print('%s, %s' % (row[0], row[1]))
    