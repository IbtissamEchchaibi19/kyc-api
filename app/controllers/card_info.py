from flask import jsonify
from io import BytesIO
import re
from app.models.user_images import get_user_image_collection
from app.utils.extract_card_info import extract_text_from_image, parse_text, extract_specific_info
from app.models.clients import get_client_by_email

def verify_card_info(username, filename):
    try:
        # Retrieve user images from the database
        user_images = get_user_image_collection(username)
        if not user_images or 'images' not in user_images:
            return jsonify({'error': 'User images not found in the database.'}), 404
        
        images = user_images['images']
        card = next((img for img in images if img['filename'] == filename), None)
        
        if not card:
            return jsonify({'error': 'Card image not found in the database.'}), 404

        # Convert binary image data to a file-like object
        card_data = card['data']
        card_file = BytesIO(card_data)
        
        # Extract text from the image
        response = extract_text_from_image(card_file)
        text = parse_text(response)
        
        # Extract specific information from the text
        extracted_info = extract_specific_info(text)

    except Exception as e:
        return jsonify({'error': f'Error processing card image: {str(e)}'}), 500
    
    # Retrieve client data
    client = get_client_by_email(username)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    first_name = client['firstname'].lower()
    last_name = client['lastname'].lower()
    id_card = client['idcard'].lower()

    # Check if extracted full name and ID card match client data
    full_name_matched = False
    id_card_verified = False

    if extracted_info['Full Name']:
        extracted_full_name = " ".join(extracted_info['Full Name']).lower()
        full_name_matched = (first_name in extracted_full_name) and (last_name in extracted_full_name)
    
    if extracted_info['ID Card']:
        id_card_verified = extracted_info['ID Card'].strip().lower() == id_card
    
    # Return separate messages for full name and card ID verification
    if full_name_matched and id_card_verified:
        return jsonify({'message': 'full name and id card verified'}), 200
    elif full_name_matched:
        return jsonify({'message': 'full name verified'}), 200
    elif id_card_verified:
        return jsonify({'message': 'id card verified'}), 200
    else:
        return jsonify({'message': 'full name and id card dismatch'}), 400
