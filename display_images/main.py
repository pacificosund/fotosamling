from google.cloud import storage

def display_images(request):
    """HTTP Cloud Function that lists GCS blobs based on a prefix.
    Args:
         request (flask.Request): The request object.
         <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """

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

    # Build a list of blob names
    #blob_names = [blob.name for blob in blobs]

    #return str(blob_names)  # Or format the output as needed 
    html_output = f'''<!DOCTYPE html>
                <html lang="en"> 
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
                    <title>Daily Images</title>
                </head>
                <body>
                '''

    #html_output += '<table>'
    row_count = 0
    images_per_row = 1  # Customize this as needed

    for blob in blobs:
        
        # public_url = blob.generate_signed_url(
        #     version="v4", expiration=600, method="GET"
        # )  # 10 minute expiration
        #public_url = f'https://storage.googleapis.com/{bucket_name}/{blob.name}'
        public_url = blob.public_url
        html_output += f'''<div><a href="{public_url}" download="{blob.name}">
                            <img src="{public_url}" width="200"></a>
                            </div>
                        '''  # Customize image width

    html_output += '</body></html>'

    return html_output

