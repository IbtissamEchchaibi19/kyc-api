from flask import Blueprint, jsonify, request
import requests
import base64
import cv2
import dlib
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
from io import BytesIO
from app.models.update_user_images import get_user_image_collection

bp = Blueprint('routes', __name__)
detector = dlib.get_frontal_face_detector()
model = InceptionResnetV1(pretrained='vggface2').eval()

def preprocess_face(face_img):
    face_img = cv2.resize(face_img, (160, 160))
    face_img = (face_img / 255.0 - 0.5) * 2
    face_img = torch.tensor(face_img).permute(2, 0, 1).unsqueeze(0).float()
    return face_img
def get_image_from_s3(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            print(f"Failed to fetch image: Status code {response.status_code}, URL: {url}")
    except Exception as e:
        print(f"Error fetching image from S3: {e}")
    return None

def get_images(username, type1, type2):
    user_images = get_user_image_collection(username)
    if not user_images or 'images' not in user_images:
        return None, None, jsonify({'error': 'User images not found in the database.'}), 404

    images = user_images['images']
    image1 = next((img for img in images if img['type'] == type1), None)
    image2 = next((img for img in images if img['type'] == type2), None)

    if not image1 or not image2:
        return None, None, jsonify({'error': 'Required images not found in the database.'}), 404

    img1_file = get_image_from_s3(image1['url'])
    img2_file = get_image_from_s3(image2['url'])

    if img1_file is None or img2_file is None:
        return None, None, jsonify({'error': 'Failed to retrieve images from S3.'}), 404

    img1 = cv2.imdecode(np.frombuffer(img1_file.read(), np.uint8), cv2.IMREAD_COLOR)
    img2 = cv2.imdecode(np.frombuffer(img2_file.read(), np.uint8), cv2.IMREAD_COLOR)

    return img1, img2, None, None

def process_and_encode_images(img1, img2):
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    faces1 = detector(gray1)
    if not faces1:
        return jsonify({'error': 'No face detected in first image.'}), 400

    x, y, w, h = (faces1[0].left(), faces1[0].top(), faces1[0].width(), faces1[0].height())
    face_img1 = img1[y:y+h, x:x+w]
    face_tensor1 = preprocess_face(face_img1)
    embedding1 = model(face_tensor1)

    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    faces2 = detector(gray2)
    if not faces2:
        return jsonify({'error': 'No face detected in second image.'}), 400

    x, y, w, h = (faces2[0].left(), faces2[0].top(), faces2[0].width(), faces2[0].height())
    face_img2 = img2[y:y+h, x:x+w]
    face_tensor2 = preprocess_face(face_img2)
    embedding2 = model(face_tensor2)

    similarity = cosine_similarity(embedding2.detach().numpy(), embedding1.detach().numpy())
    similarity_score = float(similarity[0][0])
    match_status = "Match" if similarity_score > 0.8 else "No Match"

    _, encoded_img1 = cv2.imencode('.jpg', img1)
    _, encoded_img2 = cv2.imencode('.jpg', img2)
    face_b64_1 = base64.b64encode(encoded_img1).decode('utf-8')
    face_b64_2 = base64.b64encode(encoded_img2).decode('utf-8')

    return {
        'similarity_score': similarity_score,
        'match_status': match_status,
        'image1': face_b64_1,
        'image2': face_b64_2
    }, None

def match_images(username, type1, type2):
    img1, img2, error_response, status_code = get_images(username, type1, type2)
    if error_response:
        return error_response, status_code

    result, error_response = process_and_encode_images(img1, img2)
    if error_response:
        return error_response

    return jsonify(result)

def check_faces_in_image(username, image_type):
    user_images = get_user_image_collection(username)

    if not user_images or 'images' not in user_images:
        return jsonify({'error': 'User images not found in the database.'}), 404

    # Find the specific image by type
    specific_image = next((img for img in user_images['images'] if img['type'] == image_type), None)
    
    if not specific_image:
        return jsonify({'error': 'Image not found in the database.'}), 404

    # Load image from URL
    url = specific_image['url']
    img_file = get_image_from_s3(url)
    
    if img_file is None:
        return jsonify({'error': 'Failed to fetch image from URL.'}), 404

    img_data = np.frombuffer(img_file.read(), np.uint8)
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
