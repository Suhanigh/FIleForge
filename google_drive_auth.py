import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def authenticate_google_drive():
    """Shows basic usage of the Drive v3 API.
    Prints the names and IDs of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # The file client_secrets.json stores the client ID and client secret
            # that you got from the Google API Console.
            # Rename your downloaded credentials.json to client_secrets.json
            if not os.path.exists('client_secrets.json'):
                print("Error: client_secrets.json not found. Please download your credentials from Google Cloud Console and rename it.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

if __name__ == '__main__':
    # This part is for testing the authentication flow independently
    credentials = authenticate_google_drive()
    if credentials:
        print("Authentication successful!")
        # You can now use these credentials to build a Google Drive service
        # from googleapiclient.discovery import build
        # service = build('drive', 'v3', credentials=credentials)
        # print(service)
    else:
        print("Authentication failed.") 