import functions_framework
import datetime
from google.cloud import storage
#from google.oauth2 import service_account as auth
from google.cloud.storage import Client
import uuid
import os
from io import BytesIO
import json

@functions_framework.http
def generate_shareable_link(request):
    #request_json = request.get_json(silent=True)
    #request_args = request.args
    #credentials, project_id = auth.default()
    folder_prefix = os.environ.get("FOLDER_PREFIX", f'240304/{str(uuid.uuid4())}/')
    bucket_name = os.environ.get("STORAGE_BUCKET_NAME","fotosamling")  # Fetch from environment
    #expiration_hours = int(os.environ.get('EXPIRATION_HOURS', '1')) 
    #expiration = datetime.timedelta(hours=expiration_hours)
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(folder_prefix)
    blob.upload_from_file(BytesIO())
    # url = bucket.blob(folder_prefix).generate_signed_url(
    #     version="v4",
    #     service_account_email=credentials.service_account_email,
    #     access_token=credentials.token,
    #     expiration=expiration,
    #     method="GET"  
    # )
   
    url = f"https://storage.googleapis.com/{bucket_name}/{folder_prefix}"
    json_string = json.dumps({"url": url})
    
    try:
        json_object = json.loads(json_string)
        return json_object
    except json.JSONDecodeError as e:
        response = {"error": str(e)}
        response.status_code = 400
    