import boto3
import re
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    'textract',
    region_name=os.getenv('AWS_REGION_NAME'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def extract_text_from_image(filename):
    response = client.analyze_document(
        Document={'Bytes': filename.read()},
        FeatureTypes=['FORMS']
    )
    return response

def parse_text(response):
    text_blocks = response.get('Blocks', [])
    text = " ".join([block['Text'] for block in text_blocks if block['BlockType'] == 'LINE'])
    return text

def extract_specific_info(text):
    text = text.replace('\n', ' ').strip()
    full_name = id_card = birth_date = None

    carte_index = text.find("CARTE NATIONALE D'IDENTITE")
    if carte_index != -1:
        text_after_carte = text[carte_index + len("CARTE NATIONALE D'IDENTITE"):].strip()
        born_index = text_after_carte.find('Née')
        if born_index == -1:
            born_index = text_after_carte.find('Né')
        if born_index != -1:
            names_text = text_after_carte[:born_index].strip()
            words = names_text.split()
            full_name = words

    id_card_pattern = re.compile(r'\b[A-Za-z]\d{6,}\b')
    id_card_match = id_card_pattern.search(text)
    id_card = id_card_match.group(0) if id_card_match else None

    birth_date_pattern = re.compile(r'\b(\d{2}\.\d{2}\.\d{4})\b')
    birth_date_match = birth_date_pattern.search(text)
    birth_date = birth_date_match.group(1) if birth_date_match else None

    return {
        'Full Name': full_name,
        'ID Card': id_card,
        'Birth Date': birth_date
    }
