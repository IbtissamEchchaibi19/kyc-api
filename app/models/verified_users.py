
from flask import current_app

def get_mongo():
    return current_app.extensions['pymongo']

def create_verified_record(username, match_status):
    mongo = get_mongo()
    verified_collection = mongo.db.verified

    # Only add user to collection if match_status is "Match"
    if match_status == "Match":
        result = verified_collection.update_one(
            {"username": username},
            {"$set": {"username": username, "status": match_status}},
            upsert=True
        )
        if result.modified_count > 0 or result.upserted_id:
            return {"success": "User added to verified collection successfully"}
        else:
            return {"error": "Failed to add user to verified collection"}
    else:
        # No action needed for "No Match"
        return {"success": "No user added to verified collection, status did not match"}
