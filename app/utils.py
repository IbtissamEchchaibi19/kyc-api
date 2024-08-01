import jwt
import datetime
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

def generate_login_link(email):
    token = jwt.encode({
        'sub': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    login_link = f"{current_app.config['FRONTEND_URL']}/auto-login?token={token}"
    return login_link

def send_signup_email(to_email, login_link):
    sender_email = "btissamchaibi1912@gmail.com"
    password = "kxfr oebg ujtw diyr"  # App Password

    message = MIMEMultipart("alternative")
    message["Subject"] = "face verification and detection link"
    message["From"] = sender_email
    message["To"] = to_email

    text = f" from re you verified your face : {to_email}. Use this link to login: {login_link}"
    part = MIMEText(text, "plain")
    message.attach(part)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, message.as_string())
