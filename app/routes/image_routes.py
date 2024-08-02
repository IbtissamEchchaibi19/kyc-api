from flask import Blueprint
from  app.utils.authorization import token_required
from  app.controllers.users_images import upload_image, upload_screenshot, upload_selfie, upload_card, get_screenshot, get_selfie, get_card,check_screenshot
image_bp = Blueprint('image', __name__)

@image_bp.route('/upload_image/<username>', methods=['POST'])
@token_required
def upload_image_route(username):
    return upload_image(username)

@image_bp.route('/upload-screenshot/<username>', methods=['POST'])
@token_required
def upload_screenshot_route(username):
    return upload_screenshot(username)

@image_bp.route('/upload-selfie/<username>', methods=['POST'])
@token_required
def upload_selfie_route(username):
    return upload_selfie(username)

@image_bp.route('/upload-card/<username>', methods=['POST'])
@token_required
def upload_card_route(username):
    return upload_card(username)

@image_bp.route('/get-screenshot/<username>', methods=['GET'])
@token_required
def get_screenshot_route(username):
    return get_screenshot(username)

@image_bp.route('/get-selfie/<username>', methods=['GET'])
@token_required
def get_selfie_route(username):
    return get_selfie(username)

@image_bp.route('/get-card/<username>', methods=['GET'])
@token_required
def get_card_route(username):
    return get_card(username)

@image_bp.route('/check-screenshot/<username>', methods=['GET'])
@token_required
def check_screenshot_route(username):
    return check_screenshot(username)
