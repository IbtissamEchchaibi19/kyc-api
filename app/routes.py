from flask import Blueprint, request, jsonify, current_app
from .controllers import handle_create_user, handle_login, handle_upload_image, handle_get_images, get_user_image_collection 
from functools import wraps
import jwt
from bson.objectid import ObjectId
import base64
from .models import mongo  ,delete_user_images
import cv2
import dlib
import torch
import numpy as np 
from facenet_pytorch import InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity

bp = Blueprint('routes', __name__)
detector = dlib.get_frontal_face_detector()
model = InceptionResnetV1(pretrained='vggface2').eval()

def preprocess_face(face_img):
    face_img = cv2.resize(face_img, (160, 160))
    face_img = (face_img / 255.0 - 0.5) * 2
    face_img = torch.tensor(face_img).permute(2, 0, 1).unsqueeze(0).float()
    return face_img

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing!"}), 403
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            request.username = data['sub']  # Add username to request object
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 403
        return f(*args, **kwargs)
    return decorated

@bp.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    response, status = handle_create_user(data)
    return jsonify(response), status

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    response, status = handle_login(data)
    return jsonify(response), status

@bp.route('/dashboard', methods=['GET'])
@token_required
def get_user_data():

    username = request.username

    user_data = {
        'username': username
    }

    return jsonify({'user_data': user_data}), 200


@bp.route('/upload_image/<username>', methods=['POST'])
@token_required
def upload_image(username):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    response, status = handle_upload_image(username, file)
    return jsonify(response), status


@bp.route('/upload-screenshot/<username>', methods=['POST'])
@token_required
def upload_screenshot(username):
    print(f"Received upload-screenshot request for username: {username}")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    response, status = handle_upload_image(username, "screenshot", file)
    print(f"Upload response: {response}, status: {status}")
    return jsonify(response), status

@bp.route('/upload-selfie/<username>', methods=['POST'])
@token_required
def upload_selfie(username):
    print(f"Received upload-selfie request for username: {username}")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    response, status = handle_upload_image(username, "selfie", file)
    print(f"Upload response: {response}, status: {status}")
    return jsonify(response), status

@bp.route('/check-screenshot/<username>', methods=['GET'])
@token_required
def check_screenshot(username):
    image_collection = mongo.db.images
    user_images = image_collection.find_one({"username": username})
    if user_images:
        for img in user_images.get("images", []):
            if img["type"] == "screenshot":
                return jsonify({"saved": True}), 200
    return jsonify({"saved": False}), 200

@bp.route('/upload-card/<username>', methods=['POST'])
@token_required
def upload_card(username):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    response, status = handle_upload_image(username, "card", file)
    return jsonify(response), status

@bp.route('/match_faces/<username>', methods=['POST'])
@token_required
def match_faces(username):
    # Retrieve user images from the database
    user_images = get_user_image_collection(username)
    if not user_images or 'images' not in user_images:
        return jsonify({'error': 'User images not found in the database.'}), 404

    images = user_images['images']
    screenshot_image = next((img for img in images if img['type'] == 'screenshot'), None)
    selfie_image = next((img for img in images if img['type'] == 'selfie'), None)

    if not screenshot_image or not selfie_image:
        return jsonify({'error': 'Required images not found in the database.'}), 404

    # Decode the images from binary data
    screenshot_data = np.frombuffer(screenshot_image['data'], np.uint8)
    selfie_data = np.frombuffer(selfie_image['data'], np.uint8)
    screenshot_img = cv2.imdecode(screenshot_data, cv2.IMREAD_COLOR)
    selfie_img = cv2.imdecode(selfie_data, cv2.IMREAD_COLOR)

    # Process screenshot image
    screenshot_gray = cv2.cvtColor(screenshot_img, cv2.COLOR_BGR2GRAY)
    screenshot_faces = detector(screenshot_gray)
    if not screenshot_faces:
        return jsonify({'error': 'No face detected in screenshot image.'}), 400
    x, y, w, h = (screenshot_faces[0].left(), screenshot_faces[0].top(), screenshot_faces[0].width(), screenshot_faces[0].height())
    screenshot_face_img = screenshot_img[y:y+h, x:x+w]
    screenshot_face_tensor = preprocess_face(screenshot_face_img)
    screenshot_face_embedding = model(screenshot_face_tensor)

    # Process selfie image
    selfie_gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
    selfie_faces = detector(selfie_gray)
    if not selfie_faces:
        return jsonify({'error': 'No face detected in selfie image.'}), 400
    x, y, w, h = (selfie_faces[0].left(), selfie_faces[0].top(), selfie_faces[0].width(), selfie_faces[0].height())
    selfie_face_img = selfie_img[y:y+h, x:x+w]
    selfie_face_tensor = preprocess_face(selfie_face_img)
    selfie_face_embedding = model(selfie_face_tensor)

    # Compute similarity
    similarity = cosine_similarity(selfie_face_embedding.detach().numpy(), screenshot_face_embedding.detach().numpy())
    similarity_score = float(similarity[0][0])
    match_status = "Match" if similarity_score > 0.8 else "No Match"

    # Encode images to base64 for response
    _, screenshot_encoded = cv2.imencode('.jpg', screenshot_img)
    _, selfie_encoded = cv2.imencode('.jpg', selfie_img)
    screenshot_face_b64 = base64.b64encode(screenshot_encoded).decode('utf-8')
    selfie_face_b64 = base64.b64encode(selfie_encoded).decode('utf-8')


    return jsonify({
        'similarity_score': similarity_score,
        'match_status': match_status,
        'screenshot_face_image': screenshot_face_b64,
        'selfie_face_image': selfie_face_b64
    })
    
    


@bp.route('/card_faces/<username>', methods=['POST'])
@token_required
def card_faces(username):
    # Retrieve user images from the database
    user_images = get_user_image_collection(username)
    if not user_images or 'images' not in user_images:
        return jsonify({'error': 'User images not found in the database.'}), 404

    images = user_images['images']
    screenshot_image = next((img for img in images if img['type'] == 'selfie'), None)
    selfie_image = next((img for img in images if img['type'] == 'card'), None)

    if not screenshot_image or not selfie_image:
        return jsonify({'error': 'Required images not found in the database.'}), 404

    # Decode the images from binary data
    screenshot_data = np.frombuffer(screenshot_image['data'], np.uint8)
    selfie_data = np.frombuffer(selfie_image['data'], np.uint8)
    screenshot_img = cv2.imdecode(screenshot_data, cv2.IMREAD_COLOR)
    selfie_img = cv2.imdecode(selfie_data, cv2.IMREAD_COLOR)

    # Process screenshot image
    screenshot_gray = cv2.cvtColor(screenshot_img, cv2.COLOR_BGR2GRAY)
    screenshot_faces = detector(screenshot_gray)
    if not screenshot_faces:
        return jsonify({'error': 'No face detected in screenshot image.'}), 400
    x, y, w, h = (screenshot_faces[0].left(), screenshot_faces[0].top(), screenshot_faces[0].width(), screenshot_faces[0].height())
    screenshot_face_img = screenshot_img[y:y+h, x:x+w]
    screenshot_face_tensor = preprocess_face(screenshot_face_img)
    screenshot_face_embedding = model(screenshot_face_tensor)

    # Process selfie image
    selfie_gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
    selfie_faces = detector(selfie_gray)
    if not selfie_faces:
        return jsonify({'error': 'No face detected in selfie image.'}), 400
    x, y, w, h = (selfie_faces[0].left(), selfie_faces[0].top(), selfie_faces[0].width(), selfie_faces[0].height())
    selfie_face_img = selfie_img[y:y+h, x:x+w]
    selfie_face_tensor = preprocess_face(selfie_face_img)
    selfie_face_embedding = model(selfie_face_tensor)

    # Compute similarity
    similarity = cosine_similarity(selfie_face_embedding.detach().numpy(), screenshot_face_embedding.detach().numpy())
    similarity_score = float(similarity[0][0])
    match_status = "Match" if similarity_score > 0.8 else "No Match"

    # Encode images to base64 for response
    _, screenshot_encoded = cv2.imencode('.jpg', screenshot_img)
    _, selfie_encoded = cv2.imencode('.jpg', selfie_img)
    screenshot_face_b64 = base64.b64encode(screenshot_encoded).decode('utf-8')
    selfie_face_b64 = base64.b64encode(selfie_encoded).decode('utf-8')

    return jsonify({
        'similarity_score': similarity_score,
        'match_status': match_status,
        'screenshot_face_image': screenshot_face_b64,
        'selfie_face_image': selfie_face_b64
    })


@bp.route('/check_faces_in_image/<username>/<filename>', methods=['GET'])
@token_required
def check_faces_in_image(username, filename):
    user_images =get_user_image_collection(username)

    if not user_images or 'images' not in user_images:
        return jsonify({'error': 'User images not found in the database.'}), 404

    # Find the specific image by filename
    specific_image = next((img for img in user_images['images'] if img['filename'] == filename), None)
    
    if not specific_image:
        return jsonify({'error': 'Image not found in the database.'}), 404

    img_data = np.frombuffer(specific_image['data'], np.uint8)
    img_cv = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
    
    if img_cv is None:
        return jsonify({'message': 'Invalid image'}), 400

    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    faces = detector(img_gray)
    
    # Debugging output
    print(f"Number of faces detected: {len(faces)}")

    if len(faces) == 0:
        return jsonify({'message': 'Try again, no face detected'}), 200
    else:
        for i, face in enumerate(faces):
            print(f"Face {i}: Left={face.left()}, Top={face.top()}, Width={face.width()}, Height={face.height()}")

        # Process the first detected face
        x, y, w, h = (faces[0].left(), faces[0].top(), faces[0].width(), faces[0].height())
        face_img = img_cv[y:y+h, x:x+w]
        face_tensor = preprocess_face(face_img)
        face_embedding = model(face_tensor)
        face_path = 'detected_face.jpg'
        cv2.imwrite(face_path, face_img)

        return jsonify({'message': 'Good face detected', 'face_path': face_path}), 200

@bp.route('/logout', methods=['POST'])
@token_required
def logout():
    username = request.username  # Retrieve username from request object

    # Attempt to delete all images related to the user
    deleted_count = delete_user_images(username)

    if deleted_count > 0:
        # If images were deleted, return a success message
        return jsonify({'message': 'Logged out and images cleared successfully.'}), 200
    else:
        # If no images were found or deleted, just log the user out
        return jsonify({'message': 'Logged out successfully, but no images found for deletion.'}), 200
