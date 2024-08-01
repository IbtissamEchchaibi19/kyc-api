import datetime
import jwt
from flask import current_app

def generate_token(username, expiration_minutes=60):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
    payload = {
        'sub': username,
        'exp': expiration
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token
