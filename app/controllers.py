from flask import current_app, jsonify, request
import jwt
import datetime
import cv2
import dlib
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
import base64
from .models import create_user, find_user_by_username, update_user_images, get_user_image_collection ,get_all_client_emails
from .utils import generate_login_link, send_signup_email
from . import bcrypt

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


detector = dlib.get_frontal_face_detector()
model = InceptionResnetV1(pretrained='vggface2').eval()

def preprocess_face(face_img):
    face_img = cv2.resize(face_img, (160, 160))
    face_img = (face_img / 255.0 - 0.5) * 2
    face_img = torch.tensor(face_img).permute(2, 0, 1).unsqueeze(0).float()
    return face_img
def handle_create_user(data):
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default to 'user' if not provided

    if not username or not password:
        return {"error": "Missing username or password"}, 400

    result = create_user(username, password, role)
    return {"username": username}, 201
# def handle_create_user(data):
#     username = data.get('username')
#     password = data.get('password')
    
#     if not username or not password:
#         return {"error": "Missing username or password"}, 400
    
#     result = create_user(username, password)
#     return {"username": username}, 201

# def handle_login(data):
#     username = data.get('username')
#     password = data.get('password')
    
#     if not username or not password:
#         return {"error": "Missing username or password"}, 400

#     user = find_user_by_username(username)
    
#     if user and bcrypt.check_password_hash(user['password'], password):
#         token = jwt.encode({
#             'sub': username,
#             'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
#         }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
#         return {"token": token}, 200
#     else:
#         return {"error": "Invalid username or password"}, 401
def handle_login(data):
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return {"error": "Missing username or password"}, 400

    user = find_user_by_username(username)
    
    if user and  bcrypt.check_password_hash(user['password'], password):
        token = jwt.encode({
            'sub': username,
            'role': user.get('role', 'user'),  # Include user role in the token
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return {"token": token, "role": user.get('role', 'user')}, 200
    else:
        return {"error": "Invalid username or password"}, 401
def handle_upload_image(username, image_type, file):
    if file:
        result = update_user_images(username, image_type, file)
        if "success" in result:
            return {"message": "Image uploaded successfully"}, 201
        else:
            return {"error": result["error"]}, 500

def handle_get_images(username):
    user_images = get_user_image_collection(username)
    if user_images and "images" in user_images:
        return {"images": user_images["images"]}, 200
    else:
        return {"error": "No images found"}, 404
def exist_faces():
    # Fetch the user's image collection from the database
    user_images = get_user_image_collection(request.username)

    if user_images and "images" in user_images:
        images = user_images["images"]
        
        screenshot_image = next((img for img in images if img["type"] == "screenshot"), None)
        selfie_image = next((img for img in images if img["type"] == "selfie"), None)

        if screenshot_image and selfie_image:
            # Decode the image data from the database
            screenshot_img = cv2.imdecode(np.frombuffer(screenshot_image['data'], np.uint8), cv2.IMREAD_COLOR)
            selfie_img = cv2.imdecode(np.frombuffer(selfie_image['data'], np.uint8), cv2.IMREAD_COLOR)

            # For demonstration, using one of these images as the "capture" image
            capture_img = selfie_img  # Use whichever image you want for comparison

            if capture_img is None:
                return jsonify({'message': 'Invalid image'}), 400

            capture_gray = cv2.cvtColor(capture_img, cv2.COLOR_BGR2GRAY)
            capture_faces = detector(capture_gray)
            
            if not capture_faces:
                return jsonify({'message': 'Try again, no face detected in capture image'}), 200

            x, y, w, h = (capture_faces[0].left(), capture_faces[0].top(), capture_faces[0].width(), capture_faces[0].height())
            capture_face_img = capture_img[y:y+h, x:x+w]
            capture_face_tensor = preprocess_face(capture_face_img)
            capture_face_embedding = model(capture_face_tensor)

            # Compare screenshots with capture
            screenshot_gray = cv2.cvtColor(screenshot_img, cv2.COLOR_BGR2GRAY)
            screenshot_faces = detector(screenshot_gray)
            if screenshot_faces:
                x, y, w, h = (screenshot_faces[0].left(), screenshot_faces[0].top(), screenshot_faces[0].width(), screenshot_faces[0].height())
                screenshot_face_img = screenshot_img[y:y+h, x:x+w]
                screenshot_face_tensor = preprocess_face(screenshot_face_img)
                screenshot_face_embedding = model(screenshot_face_tensor)
                
                screenshot_similarity = cosine_similarity(capture_face_embedding.detach().numpy(), screenshot_face_embedding.detach().numpy())
                screenshot_match_status = "Match" if screenshot_similarity[0][0] > 0.8 else "No Match"

                # Compare selfies with capture
                selfie_gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
                selfie_faces = detector(selfie_gray)
                if selfie_faces:
                    x, y, w, h = (selfie_faces[0].left(), selfie_faces[0].top(), selfie_faces[0].width(), selfie_faces[0].height())
                    selfie_face_img = selfie_img[y:y+h, x:x+w]
                    selfie_face_tensor = preprocess_face(selfelfie_face_img)
                    selfie_face_embedding = model(selfie_face_tensor)
                    
                    selfie_similarity = cosine_similarity(capture_face_embedding.detach().numpy(), selfie_face_embedding.detach().numpy())
                    selfie_match_status = "Match" if selfie_similarity[0][0] > 0.8 else "No Match"
                    
                    return jsonify({
                        'screenshot_match_status': screenshot_match_status,
                        'selfie_match_status': selfie_match_status
                    }), 200
                else:
                    return jsonify({'message': 'No face detected in selfie image'}), 400
            else:
                return jsonify({'message': 'No face detected in screenshot image'}), 400
        else:
            return jsonify({'message': 'Screenshot or selfie image missing'}), 404
    else:
        return jsonify({'message': 'No images found for user'}), 404

def match_faces():
    # Fetch the user's image collection from the database
    user_images = get_user_image_collection(request.username)

    if user_images and "images" in user_images:
        images = user_images["images"]
        
        card_image = next((img for img in images if img["type"] == "card"), None)
        selfie_image = next((img for img in images if img["type"] == "selfie"), None)

        if card_image and selfie_image:
            # Decode the image data from the database
            card_img = cv2.imdecode(np.frombuffer(card_image['data'], np.uint8), cv2.IMREAD_COLOR)
            selfie_img = cv2.imdecode(np.frombuffer(selfie_image['data'], np.uint8), cv2.IMREAD_COLOR)

            # Process and compare card and selfie images
            card_gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            card_faces = detector(card_gray)
            if not card_faces:
                return jsonify({'error': 'No face detected in card image.'}), 400

            x, y, w, h = (card_faces[0].left(), card_faces[0].top(), card_faces[0].width(), card_faces[0].height())
            card_face_img = card_img[y:y+h, x:x+w]
            card_face_tensor = preprocess_face(card_face_img)
            card_face_embedding = model(card_face_tensor)

            selfie_gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
            selfie_faces = detector(selfie_gray)
            if not selfie_faces:
                return jsonify({'error': 'No face detected in selfie image.'}), 400

            x, y, w, h = (selfie_faces[0].left(), selfie_faces[0].top(), selfie_faces[0].width(), selfie_faces[0].height())
            selfie_face_img = selfie_img[y:y+h, x:x+w]
            selfie_face_tensor = preprocess_face(selfie_face_img)
            selfie_face_embedding = model(selfie_face_tensor)

            similarity = cosine_similarity(selfie_face_embedding.detach().numpy(), card_face_embedding.detach().numpy())
            similarity_score = float(similarity[0][0])
            match_status = "Match" if similarity_score > 0.8 else "No Match"

            # Save images for return
            card_face_path = 'detected_card_face.jpg'
            selfie_face_path = 'detected_selfie_face.jpg'
            cv2.imwrite(card_face_path, card_face_img)
            cv2.imwrite(selfie_face_path, selfie_face_img)

            with open(card_face_path, "rb") as f:
                card_face_b64 = base64.b64encode(f.read()).decode('utf-8')
            with open(selfie_face_path, "rb") as f:
                selfie_face_b64 = base64.b64encode(f.read()).decode('utf-8')

            return jsonify({
                'similarity_score': similarity_score,
                'match_status': match_status,
                'card_face_image': card_face_b64,
                'selfie_face_image': selfie_face_b64
            }), 200
        else:
            return jsonify({'message': 'Card or selfie image missing'}), 404
    else:
        return jsonify({'message': 'No images found for user'}), 404


def notify_all_clients():
    client_emails = get_all_client_emails()
    if not client_emails:
        print("No clients to notify")
        return
    
    for email in client_emails:
        try:
            login_link = generate_login_link(email)
            send_signup_email(email, login_link)
            print(f"Sent email to {email}")
        except Exception as e:
            print(f"Failed to send email to {email}: {str(e)}")
