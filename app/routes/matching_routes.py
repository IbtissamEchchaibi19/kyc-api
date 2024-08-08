from flask import Blueprint
from  app.utils.authorization import token_required
from  app.controllers.cv_model import match_faces, card_faces
from  app.utils.cv_model import check_faces_in_image

matching_bp = Blueprint('matching', __name__)

@matching_bp.route('/match_faces/<username>', methods=['POST'])
@token_required
def match_faces_route(username):
    return match_faces(username)

@matching_bp.route('/card_faces/<username>', methods=['POST'])
@token_required
def card_faces_route(username):
    return card_faces(username)

@matching_bp.route('/check_faces_in_image/<username>/<image_type>', methods=['GET'])
@token_required
def check_faces_in_image_route(username, image_type):
    print(f"Username received in route: {username}")
    print(f"Image type received in route: {image_type}")
    return check_faces_in_image(username, image_type)