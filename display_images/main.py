from google.cloud import storage
import requests

def display_images(request):
    # Extract bucket and prefix from request (consider adding validation)
    bucket_name = request.args.get('bucket_name')
    #prefix = request.args.get('prefix')

    if not bucket_name:
        return 'Missing required parameters: bucket_name and prefix', 400

    # Create a Storage client
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.get_bucket(bucket_name)

    # List blobs with the specified prefix
    blobs = bucket.list_blobs(prefix=None)

    html_output = f'''<!DOCTYPE html>
                <html lang="en"> 
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
                    <title>Daily Images</title>
                </head>
                <body>
                '''
    for blob in blobs:
        public_url = blob.public_url
        try:
            response = requests.head(public_url)
            if response.status_code == 200:
                html_output += f'''<div><a href="{public_url}" download="{blob.name}" align="center">
                                    <p align="center">{blob.name}</p>
                                    <img src="{public_url}" width="200" alt="Check back soon!"></a>
                                    </div>
                                '''
            else:
                html_output += f'''<div><h1 align="center">Check back soon!
                    </div>
                '''
        except requests.exceptions.RequestException:
            html_output += f'''<div><h1 align="center">Check back soon!
            '''  

    html_output += '</body></html>'

    return html_output

