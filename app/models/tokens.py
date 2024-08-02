from flask import current_app

def get_mongo():
    return current_app.extensions['pymongo']

def save_token_to_db(email, token, used=False):
    mongo = get_mongo()
    tokens_collection = mongo.db.tokens
    result = tokens_collection.update_one(
        {'email': email, 'token': token},
        {'$set': {'used': used}},
        upsert=True
    )
    print(f"MongoDB update result: {result.raw_result}")  # Debug print statement
    return result.modified_count > 0

def is_token_used(token):
    mongo = get_mongo()
    tokens_collection = mongo.db.tokens
    token_entry = tokens_collection.find_one({'token': token})
    return token_entry is not None and token_entry.get('used', False)

def mark_token_as_used(token):
    mongo = get_mongo()
    tokens_collection = mongo.db.tokens
    result = tokens_collection.update_one(
        {'token': token},
        {'$set': {'used': True}}
    )
    print(f"MongoDB mark as used result: {result.raw_result}")  # Debug print statement
    return result.modified_count > 0
