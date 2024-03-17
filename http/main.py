from flask import jsonify
import functions_framework
import json
import os
import re
import requests
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Assuming CONFIG is automatically populated with the JSON secret content
CONFIG = json.loads(os.getenv("CONFIG"))

def is_email_valid(email):
    """Check if the email address is valid."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)

def is_recaptcha_valid(recaptcha_response, domain):
    """Verify reCAPTCHA response with Google's API."""
    if domain == CONFIG['VALIDATION_DOMAIN']:
        secret_key = CONFIG['DOMAIN_CONFIG'].get(domain, {}).get('secret_key', '')
        return recaptcha_response == secret_key

    secret_key = CONFIG['DOMAIN_CONFIG'].get(domain, {}).get('recaptcha_secret_key', '')
    verification_url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {'secret': secret_key, 'response': recaptcha_response}
    response = requests.post(verification_url, data=payload)
    result = response.json()
    return result.get('success', False)

def make_response_with_cors(body, status=200, origin='*'):
    """Create a Flask response with CORS headers."""
    response = jsonify(body)
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response, status

def send_email(form_data, domain):
    """Send email based on form data and domain config."""
    domain_config = CONFIG['DOMAIN_CONFIG'].get(domain, {})
    to_address = domain_config.get('recipient', '')
    subject = f"{CONFIG.get('SMTP_SUBJECT', 'No Subject')} - {domain}"
    from_address = f'"{CONFIG["SMTP_FROM_NAME"]}" <{CONFIG["SMTP_FROM_EMAIL"]}>'
    
    if "email" not in form_data or not is_email_valid(form_data.get("email")):
        return {'success': False, 'message': 'Invalid sender email address.'}, 400
    
    if not is_email_valid(to_address):
        return {'success': False, 'message': 'Invalid recipient email address.'}, 400    

    mail_body = ''
    for field_key, field_label in domain_config.get('email_body_fields', {}).items():
        if field_key in form_data:
            value = form_data.get(field_key, '')
            mail_body += f'{field_label}: {value}\n'
        else:
            continue  # Optionally handle the absence of expected data

    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.add_header('Reply-To', form_data.get("email"))
    msg.attach(MIMEText(mail_body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP_SSL(CONFIG['SMTP_HOST'], CONFIG['SMTP_PORT'], context=ssl.create_default_context()) as server:
            server.login(CONFIG['SMTP_USERNAME'], CONFIG['SMTP_PASSWORD'])
            server.send_message(msg)
        return {'success': True, 'message': CONFIG['SUCCESS_MESSAGE']}, 200
    except smtplib.SMTPException as e:
        return {'success': False, 'message': f"Email sending failed. Error: {str(e)}"}, 500

@functions_framework.http
def handler(request):
    """Handle incoming requests."""
    origin = request.headers.get('Origin', '*')
    
    if request.method == "OPTIONS":
        return make_response_with_cors({}, 204, origin=origin)

    if request.method != 'POST':
        return make_response_with_cors({'success': False, 'message': 'Method not allowed'}, 405, origin=origin)

    domain = origin.split("//")[-1].split("/")[0].lower().replace('www.', '')
    if domain not in {d.replace('www.', '') for d in CONFIG['DOMAIN_CONFIG'].keys()}:
        return make_response_with_cors({'success': False, 'message': 'Origin domain is not allowed.'}, 403, origin=origin)

    form_data = request.json if request.is_json else request.form.to_dict()
    
    # Validate required fields
    missing_fields = [field for field in CONFIG.get('REQUIRED_FIELDS', '').split(',') if not form_data.get(field)]
    if missing_fields:
        return make_response_with_cors({'success': False, 'message': 'Required fields missing.'}, 400, origin=origin)

    if not is_recaptcha_valid(form_data.get('g-recaptcha-response'), domain):
        return make_response_with_cors({'success': False, 'message': 'reCAPTCHA validation failed.'}, 400, origin=origin)

    response_body, status = send_email(form_data, domain)
    return make_response_with_cors(response_body, status, origin=origin)