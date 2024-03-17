import functions_framework
import qrcode
from io import BytesIO
from PIL import Image
import flask
import base64
import uuid
import os
from google.cloud.storage import Client
from datetime import datetime

now = datetime.now()

function_url = os.environ.get('FUNCTION_URL')
location = os.environ.get('LOCATION')
src_bucket = os.environ.get('SRC_BUCKET')
src_blob = os.environ.get('SRC_BLOB')


@functions_framework.http
def generate_qrcode(request):
    request_json = request.get_json(silent=True)
    request_args = request.args
    
    # Create prefix
    datetime_string = now.strftime('%Y-%m-%d-%H-%M-%S')
    bucket_name = str(uuid.uuid4())
    #link_prefix = f'{datetime_string}'
    blob_prefix = f'check_back_soon'
    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)
    bucket.location = location
    bucket = storage_client.create_bucket(bucket)
    #bucket.iam_configuration.uniform_bucket_level_access_enabled = True
    #bucket.patch()
    bucket.acl.all().grant_read()
    bucket.acl.save()
    #acl = [{'role': 'STORAGE_OBJECT_VIEWER', 'entity': 'allUsers'}]
    #bucket.acl.save(acl=acl)
    blob = bucket.blob(blob_prefix)
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

    html_output += '<table>'
    row_count = 0
    images_per_row = 1  # Customize this as needed

    html_output += f'''<td><a href="{data_uri}" download="{data_uri}">
                        <img src="{data_uri}" width="375px" height="375"></a>
                        </td>
                    '''  # Customize image width

    row_count += 1
    if row_count >= images_per_row:
        html_output += '</tr>'
        row_count = 0

    if row_count > 0:  # Close the last row if open
        html_output += '</tr>'

    html_output += '</table></body></html>'

    return html_output