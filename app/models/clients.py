from flask import current_app

def get_mongo():
    return current_app.extensions['pymongo']

def create_client(company, email):
    mongo = get_mongo()
    clients_collection = mongo.db.clients
    if clients_collection.find_one({"email": email}):
        return {"error": "Client already exists"}
    client_data = {
        "company": company,
        "email": email
    }
    result = clients_collection.insert_one(client_data)
    if result.inserted_id:
        return {"success": "Client added successfully"}
    else:
        return {"error": "Failed to add client"}

def client_exists(email):
    mongo = get_mongo()
    clients_collection = mongo.db.clients
    return clients_collection.find_one({"username": email}) is not None

def get_all_clients():
    mongo = get_mongo()
    clients_collection = mongo.db.clients
    clients = clients_collection.find()
    return [{"company": client["company"], "email": client["email"]} for client in clients]

def get_all_client_emails():
    mongo = get_mongo()
    clients_collection = mongo.db.clients
    clients = clients_collection.find({}, {"email": 1, "_id": 0})
    return [client["email"] for client in clients]
