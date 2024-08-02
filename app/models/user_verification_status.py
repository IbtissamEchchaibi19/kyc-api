from flask import current_app

def get_mongo():
    return current_app.extensions['pymongo']

def create_verification_status(username, status):
    mongo = get_mongo()
    verification_status_collection = mongo.db.verification_statuses
    result = verification_status_collection.update_one(
        {"username": username},
        {"$set": {"status": status}},
        upsert=True
    )
    if result.modified_count > 0 or result.upserted_id:
        return {"success": "Verification status updated successfully"}
    else:
        return {"error": "Failed to update verification status"}
