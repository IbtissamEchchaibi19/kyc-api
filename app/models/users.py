from flask import current_app

def get_mongo():
    return current_app.extensions['pymongo']

def get_bcrypt():
    return current_app.extensions['bcrypt']

def create_user(username, password, role='user'):
    bcrypt = get_bcrypt()
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = {
        "username": username,
        "password": hashed_password,
        "role": role
    }
    mongo = get_mongo()
    result = mongo.db.users.insert_one(user)
    return result

def find_user_by_username(username):
    mongo = get_mongo()
    return mongo.db.users.find_one({"username": username})
