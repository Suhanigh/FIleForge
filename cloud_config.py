import json
import os
import pickle

CONFIG_DIR = os.path.join(os.path.expanduser('~/'), '.fileforge')
GOOGLE_CREDS_FILE = os.path.join(CONFIG_DIR, 'google_credentials.json')

def ensure_config_dir_exists():
    """Ensures the configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def save_google_credentials(credentials):
    """Saves Google Drive credentials to a file."""
    ensure_config_dir_exists()
    try:
        # Convert credentials to a serializable dictionary
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        with open(GOOGLE_CREDS_FILE, 'w') as f:
            json.dump(creds_dict, f)
        print(f"Google credentials saved to {GOOGLE_CREDS_FILE}")
    except Exception as e:
        print(f"Error saving Google credentials: {e}")

def load_google_credentials():
    """Loads Google Drive credentials from a file."""
    if os.path.exists(GOOGLE_CREDS_FILE):
        try:
            with open(GOOGLE_CREDS_FILE, 'r') as f:
                creds_dict = json.load(f)
            # Recreate credentials object from dictionary
            from google.oauth2.credentials import Credentials # Import here to avoid circular dependency if used elsewhere
            creds = Credentials(
                token=creds_dict.get('token'),
                refresh_token=creds_dict.get('refresh_token'),
                token_uri=creds_dict.get('token_uri'),
                client_id=creds_dict.get('client_id'),
                client_secret=creds_dict.get('client_secret'),
                scopes=creds_dict.get('scopes')
            )
            print(f"Google credentials loaded from {GOOGLE_CREDS_FILE}")
            return creds
        except Exception as e:
            print(f"Error loading Google credentials: {e}")
            return None
    return None

def clear_google_credentials():
    """Deletes the saved Google Drive credentials file."""
    if os.path.exists(GOOGLE_CREDS_FILE):
        try:
            os.remove(GOOGLE_CREDS_FILE)
            print(f"Google credentials file deleted: {GOOGLE_CREDS_FILE}")
        except Exception as e:
            print(f"Error deleting Google credentials file: {e}")

# Note on security: Storing credentials in a local file, even in a hidden directory,
# is not as secure as using a system-level credential manager.
# For a production application, consider using libraries like `keyring`. 