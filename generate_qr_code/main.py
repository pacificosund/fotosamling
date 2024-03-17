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

bucket_name = os.environ.get('BUCKET_NAME')
function_url = os.environ.get('FUNCTION_URL')

@functions_framework.http
def generate_qrcode(request):
    request_json = request.get_json(silent=True)
    request_args = request.args
    
    # Create prefix
    datetime_string = now.strftime('%Y-%m-%d-%H-%M-%S')
    random = str(uuid.uuid4())
    link_prefix = f'{random}'
    bucket_prefix = f'{link_prefix}/{datetime_string}'
    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(bucket_prefix)
    blob.upload_from_file(BytesIO())
    link = f'{function_url}?bucket_name={bucket_name}&prefix={link_prefix}'
    
    # 
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
                    <title>Daily Images</title>
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