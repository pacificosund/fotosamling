import functions_framework
import qrcode
from PIL import Image
from io import BytesIO
import base64
import uuid
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timezone
import logging

function_url = os.environ.get('FUNCTION_URL')
location = os.environ.get('LOCATION')
function_timezone = os.environ.get('TIMEZONE')

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.environment.get('SERVICE_ACCOUNT_FILE')

function_timezone_delta = timezone(datetime.strptime(function_timezone, '%z').utcoffset())
now = datetime.now(tz=function_timezone_delta)

def create_folder(credentials: Credentials, folder_name='') -> None:
    # Build the Drive service
    service = build('drive', 'v3', credentials=credentials)

    # Create the folder metadata
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    # Create the folder
    folder = service.files().create(body=folder_metadata).execute()

    folder_id = folder.get('id')
    logging.info(f'Folder ID: {folder_id}')

    # Create permissions
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    service.permissions().create(fileId=folder_id, body=permission).execute()
    
    share_link = folder.get('webViewLink')
    logging.info(f'Share link: {share_link}') 

    return {
        'folder_name': folder_name,
        'shareable_link': share_link
    }

@functions_framework.http
def generate_qrcode(request):
    request_json = request.get_json(silent=True)
    request_args = request.args
    
    # Get credentials
    creds = Credentials.from_json(SERVICE_ACCOUNT_FILE, SCOPES)
             
    # Create prefix
    #datetime_string = now.strftime('%Y-%m-%d-%H-%M-%S')
    #datetime_web = now.strftime('%Y-%m-%d %H:%M:%S')
    folder_name = str(uuid.uuid4())
    
    # Create bucket
    folder = create_folder(creds, folder_name)
    
    # Generate QR code
    link = folder['shareable_link']
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="white", back_color="black")

    # Save the image to a bytes buffer
    image_buffer = BytesIO()
    img.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    encoded_image = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
    data_uri = f'data:image/png;base64,{encoded_image}'

    # Return the image as a response
    html_output = f'''<!DOCTYPE html>
                <html lang="en"> 
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
                    <title>See your photos here in 24 hours!</title>
                </head>
                <body>
                '''

    html_output += f'''<div><a href="{data_uri}" download="{data_uri}">
                    <img src="{data_uri}" width="350px" height="350px" alt="QR code">
                    </a>
                    '''

    html_output += f'<div><a href="{link}">Generated at: {datetime_web}</a></div>'
 
    html_output += '</body></html>'

    return html_output

if __name__ == '__main__':
    generate_qrcode(None)