from flask import request ,current_app ,jsonify ,current_app
from  app.models.user_images import *

def get_mongo():
    return current_app.extensions['pymongo']



def upload_image(username):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    response, status = handle_upload_image(username, file)
    return jsonify(response), status

def handle_upload_image(username, image_type, file):
    if file:
        result = update_user_images(username, image_type, file)
        if "success" in result:
            return {"message": "Image uploaded successfully"}, 201
        else:
            return {"error": result["error"]}, 500

def upload_image(username, image_type):
    print(f"Received upload-{image_type} request for username: {username}")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    response, status = handle_upload_image(username, image_type, file)
    print(f"Upload response: {response}, status: {status}")
    return jsonify(response), status

def upload_screenshot(username):
    return upload_image(username, "screenshot")

def upload_selfie(username):
    return upload_image(username, "selfie")

def upload_card(username):
    return upload_image(username, "card")

def handle_get_images(username):
    user_images = get_user_image_collection(username)
    if user_images and "images" in user_images:
        return {"images": user_images["images"]}, 200
    else:
        return {"error": "No images found"}, 404
    
def check_screenshot(username):
    mongo= get_mongo()
    image_collection = mongo.db.images
    user_images = image_collection.find_one({"username": username})
    if user_images:
        for img in user_images.get("images", []):
            if img["type"] == "screenshot":
                return jsonify({"saved": True}), 200
    return jsonify({"saved": False}), 200

def get_screenshot(username):
    return get_image(username, "screenshot")

def get_card(username):
    return get_image(username, "card")

def get_selfie(username):
    return get_image(username, "selfie")
