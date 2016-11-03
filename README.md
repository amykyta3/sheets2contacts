# sheets2contacts
Update Google contacts using a Google sheets document

## Installing Dependencies

```
sudo pip2 install gdata google-api-python-client
sudo apt-get install python-httplib2 python-oauth2client
```

## Set up Google App

* Use the following wizards to enable the Google Sheets and Google Contacts APIs
    * https://console.developers.google.com/start/api?id=people.googleapis.com
    * https://console.developers.google.com/start/api?id=sheets.googleapis.com
    * https://console.developers.google.com/start/api?id=contacts-json.googleapis.com
* Create credentials for the two APIs:
    * https://console.developers.google.com/apis/credentials
    * Click "Create Credentials"--> "OAuth client ID"
    * Select "other" and name it "sheets2contacts"
    * Once created, download the JSON file.
    * Save it as 'client_id.json' in the same folder as sheets2contacts.py

## Sync!
Example source address book: https://docs.google.com/spreadsheets/d/16E0UPFYSgJK18hsiwfHgr27c0suVjR0ilYO9PjKpx18/edit?usp=sharing
Sync with google contacts by:

```
./sheets2contacts.py --sheet <URL>
```

1. For first-time run, a browser will open asking you to login to your Google account to authenticate access to Sheets and Contacts
2. Contacts will get synced to your account
    * All contacts synced are placed into group "Synced with sheets2contacts", as well as other groups specified in the sheet.
    * Contacts only get deleted if they are a member of the "Synced with sheets2contacts" group.
