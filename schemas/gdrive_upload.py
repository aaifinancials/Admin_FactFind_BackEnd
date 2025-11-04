import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials

def get_root_folder(service, root_name="AAI Financials Mortgage Customers"):
    response = service.files().list(
        q=f"name='{root_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()

    if response["files"]:
        return response["files"][0]["id"]

    folder_metadata = {
        "name": root_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]

def get_customer_folder(service, root_folder_id, customer_id):
    response = service.files().list(
        q=f"name='{customer_id}' and '{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()

    if response["files"]:
        return response["files"][0]["id"]

    folder_metadata = {
        "name": customer_id,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [root_folder_id],
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]

def get_drive_service():
    """Authenticate and return a Google Drive service client."""
    creds = Credentials.from_authorized_user_file(
        "credentials.json",
        ["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

async def upload_file_to_drive(drive_service, customer_folder_id, file):
    """Uploads file directly to Drive (no local storage)."""
    file_content = await file.read()  # read file in memory
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=file.content_type)
    file_metadata = {
        "name": file.filename,
        "parents": [customer_folder_id],
    }

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink"
    ).execute()

    return {
        "file_name": uploaded["name"],
        "google_drive_id": uploaded["id"],
        "download_link": uploaded["webViewLink"],
    }