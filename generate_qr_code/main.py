import functions_framework
import qrcode
from PIL import Image
from io import BytesIO
import base64
import uuid
import os
from google.cloud import storage
#from google.cloud import iam_v2
from datetime import datetime, timezone
import logging

function_url = os.environ.get('FUNCTION_URL')
location = os.environ.get('LOCATION')
src_bucket = os.environ.get('SRC_BUCKET')
src_blob = os.environ.get('SRC_BLOB')
function_timezone = os.environ.get('TIMEZONE')

function_timezone_delta = timezone(datetime.strptime(function_timezone, '%z').utcoffset())
now = datetime.now(tz=function_timezone_delta)

@functions_framework.http
def generate_qrcode(request):
    request_json = request.get_json(silent=True)
    request_args = request.args
    
    # Create prefix
    datetime_string = now.strftime('%Y-%m-%d-%H-%M-%S')
    datetime_web = now.strftime('%Y-%m-%d %H:%M:%S')
    bucket_name = str(uuid.uuid4())
    
    # check buckets
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()
    num_buckets = len(list(buckets))
    if num_buckets > 20:
        logging.error("Too many blobs in the bucket")
        return 'Too many blobs. Please try again later., 400'
    bucket = storage_client.bucket(bucket_name)
    bucket.location = location

    # Create bucket
    blob = bucket.blob(datetime_string)
    bucket = storage_client.create_bucket(bucket)
    bucket.iam_configuration.uniform_bucket_level_access_enabled = True
    bucket.patch()
    # iam_client = iam_v2.IAMPolicyClient()
    # policy = iam_client.get_iam_policy(request={'resource': bucket.name})
    # binding = policy.bindings.add()
    # binding.role = 'roles/storage.objectViewer'
    # binding.members.append('allUsers')
    # iam_client.set_iam_policy(request={'resource': bucket.name, 'policy': policy})
    #bucket.acl.all().grant_read()
    #bucket.acl.save()
    #acl = [{'role': 'STORAGE_OBJECT_VIEWER', 'entity': 'allUsers'}]
    #bucket.acl.save(acl=acl)
    
    # Copy default image
 
    bucket_source = storage_client.bucket(src_bucket)
    blob_source = bucket_source.blob(src_blob)
    bucket_source.copy_blob(blob_source, bucket, datetime_string)
    #blob.upload_from_file(BytesIO())
    link = f'{function_url}?bucket_name={bucket_name}'
    
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