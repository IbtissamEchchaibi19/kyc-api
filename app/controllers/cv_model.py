from  app.utils.cv_model import *
from  app.models.user_verification_status import   create_verification_status
from  app.models.verified_users import  create_verified_record


def match_faces(username):
    return match_images(username, 'screenshot', 'selfie')

def card_faces(username):
    response = match_images(username, 'selfie', 'card')
    # Extract data and status code from the response
    if response.status_code == 200:
        result = response.get_json()
        create_verification_status(username, result['match_status'])
        if result['match_status'] == "Match":
            create_verified_record(username, result['match_status'])
    return response
