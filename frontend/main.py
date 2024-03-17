from flask import Flask, render_template, request
import os
import requests 

app = Flask(__name__)

# Replace with the names of your deployed functions
SHAREABLE_LINK_FUNCTION_URL = 'https://...' 
QR_CODE_FUNCTION_URL = 'https://...' 


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        blob_name = request.form['blob_name']

        # Step 1: Get shareable link
        response = requests.post(SHAREABLE_LINK_FUNCTION_URL, data={'blob_name': blob_name})
        shareable_link = response.text  

        # Step 2: Get QR code
        response = requests.post(QR_CODE_FUNCTION_URL, data={'link': shareable_link})
        qr_code_image = response.text 

        return render_template('index.html', qr_code_image=qr_code_image) 

    else:
        return render_template('index.html') 

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host='0.0.0.0', port=port) 
