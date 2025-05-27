from __future__ import print_function

import io
import os.path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

def list_google_drive_files(credentials, folder_id='root'):
    """Lists files and folders in a specified Google Drive folder.

    Args:
        credentials: Google OAuth2 credentials object.
        folder_id: The ID of the folder to list files from. Defaults to 'root'.

    Returns:
        A list of dictionaries, each representing a file or folder, or None if an error occurs.
    """
    try:
        service = build('drive', 'v3', credentials=credentials)

        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false", # Query to list children of the folder, excluding trashed items
            pageSize=1000, # Increase page size to get more results per request
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            orderBy="name").execute()
        
        items = results.get('files', [])

        if not items:
            print(f'No files found in folder ID: {folder_id}')
            return []
        
        # Format the results
        formatted_items = []
        for item in items:
            formatted_items.append({
                'id': item['id'],
                'name': item['name'],
                'mimeType': item['mimeType'],
                'modifiedTime': item['modifiedTime'],
                'is_folder': item['mimeType'] == 'application/vnd.google-apps.folder'
            })
        return formatted_items

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An API error occurred: {error}')
        return None
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return None

def download_google_drive_file(credentials, file_id, file_path):
    """Downloads a file from Google Drive.

    Args:
        credentials: Google OAuth2 credentials object.
        file_id: The ID of the file to download.
        file_path: The local path to save the downloaded file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        service = build('drive', 'v3', credentials=credentials)
        
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%") # Basic progress printing
        return True

    except HttpError as error:
        print(f'An API error occurred: {error}')
        return False
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return False

def upload_google_drive_file(credentials, file_path, folder_id='root'):
    """Uploads a file to a specified Google Drive folder.

    Args:
        credentials: Google OAuth2 credentials object.
        file_path: The local path of the file to upload.
        folder_id: The ID of the folder to upload the file to. Defaults to 'root'.

    Returns:
        The ID of the uploaded file if successful, None otherwise.
    """
    try:
        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        print(f"File ID: {file.get('id')}")
        return file.get('id')

    except HttpError as error:
        print(f'An API error occurred: {error}')
        return None
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return None

def create_google_drive_folder(credentials, folder_name, parent_folder_id='root'):
    """Creates a new folder in Google Drive.

    Args:
        credentials: Google OAuth2 credentials object.
        folder_name: The name of the new folder.
        parent_folder_id: The ID of the parent folder. Defaults to 'root'.

    Returns:
        The ID of the created folder if successful, None otherwise.
    """
    try:
        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        file = service.files().create(body=file_metadata,
                                        fields='id').execute()
        print(f"Folder ID: {file.get('id')}")
        return file.get('id')

    except HttpError as error:
        print(f'An API error occurred: {error}')
        return None
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return None

def delete_google_drive_item(credentials, item_id):
    """Deletes a file or folder in Google Drive.

    Args:
        credentials: Google OAuth2 credentials object.
        item_id: The ID of the file or folder to delete.

    Returns:
        True if successful, False otherwise.
    """
    try:
        service = build('drive', 'v3', credentials=credentials)
        service.files().delete(fileId=item_id).execute()
        print(f'Item with ID: {item_id} deleted.')
        return True

    except HttpError as error:
        print(f'An API error occurred: {error}')
        return False
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return False 