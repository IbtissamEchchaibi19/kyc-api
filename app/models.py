from . import mongo, bcrypt
from bson import ObjectId
from flask import send_file ,jsonify
import io 

def create_user(username, password):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = {
        "username": username,
        "password": hashed_password
    }
    result = mongo.db.users.insert_one(user)
    return result

def find_user_by_username(username):
    return mongo.db.users.find_one({"username": username})



# def update_user_images(username, image_type, file):
    image_collection = mongo.db.images
    image_data = {
        "filename": f"{image_type}.jpg",  # Change to specific type
        "content_type": file.content_type,
        "data": file.read(),
        "type": image_type  # Add a type field for differentiation
    }
    
    user_images = image_collection.find_one({"username": username})
    
    if user_images and "images" in user_images:
        images = user_images["images"]
        
        # Check if there's already an image of this type and replace it
        image_found = False
        for img in images:
            if img["type"] == image_type:
                # Replace existing image of this type
                image_data["_id"] = img["_id"]
                image_collection.update_one(
                    {"username": username, "images._id": img["_id"]},
                    {"$set": {"images.$": image_data}}
                )
                image_found = True
                break
        
        if not image_found:
            # Add new image if not found
            image_data["_id"] = str(ObjectId())
            images.append(image_data)
            result = image_collection.update_one(
                {"username": username},
                {"$set": {"images": images}}
            )
            
            if result.modified_count > 0:
                return {"success": "Image collection updated successfully"}
            else:
                return {"error": "Failed to update image collection"}
        else:
            return {"success": "Image updated successfully"}
    else:
        # Create a new image list for the user
        new_user_images = {
            "username": username,
            "images": [image_data]
        }
        result = image_collection.insert_one(new_user_images)
        
        if result.inserted_id:
            return {"success": "Image collection updated successfully"}
        else:
            return {"error": "Failed to insert new image collection"}

from bson.objectid import ObjectId

def update_user_images(username, image_type, file):
    image_collection = mongo.db.images
    image_data = {
        "filename": f"{image_type}.jpg",
        "content_type": file.content_type,
        "data": file.read(),
        "type": image_type
    }

    user_images = image_collection.find_one({"username": username})

    if user_images and "images" in user_images:
        images = user_images["images"]

        # Check if there's already an image of this type and replace it
        image_found = False
        for img in images:
            if img["type"] == image_type:
                # Replace existing image of this type
                if "_id" in img:
                    image_data["_id"] = img["_id"]
                    image_collection.update_one(
                        {"username": username, "images._id": img["_id"]},
                        {"$set": {"images.$": image_data}}
                    )
                else:
                    # If '_id' key does not exist, generate a new ObjectId and replace the image
                    image_data["_id"] = str(ObjectId())
                    images.remove(img)
                    images.append(image_data)
                    image_collection.update_one(
                        {"username": username},
                        {"$set": {"images": images}}
                    )
                image_found = True
                break

        if not image_found:
            # Add new image if not found
            image_data["_id"] = str(ObjectId())
            images.append(image_data)
            result = image_collection.update_one(
                {"username": username},
                {"$set": {"images": images}}
            )

            if result.modified_count > 0:
                return {"success": "Image collection updated successfully"}
            else:
                return {"error": "Failed to update image collection"}
        else:
            return {"success": "Image updated successfully"}
    else:
        # Create a new image list for the user
        new_user_images = {
            "username": username,
            "images": [image_data]
        }
        result = image_collection.insert_one(new_user_images)

        if result.inserted_id:
            return {"success": "Image collection updated successfully"}
        else:
            return {"error": "Failed to insert new image collection"}

def create_verification_status(username, status):
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
    
def create_verified_record(username, match_status):
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

def add_user_to_verified(username):
    verified_collection = mongo.db.verified
    result = verified_collection.update_one(
        {"username": username},
        {"$set": {"username": username}},
        upsert=True
    )
    if result.modified_count > 0 or result.upserted_id:
        return {"success": "User added to verified collection successfully"}
    else:
        return {"error": "Failed to add user to verified collection"}

def get_user_image_collection(username):
    return mongo.db.images.find_one({"username": username})

def get_image(username, image_type):
    image_collection = mongo.db.images
    user_images = image_collection.find_one({"username": username})
    
    if user_images and "images" in user_images:
        for img in user_images["images"]:
            if img["type"] == image_type:
                return send_file(
                    io.BytesIO(img["data"]),
                    mimetype=img["content_type"],
                    as_attachment=True,
                    download_name=img["filename"]  # Use 'download_name' instead of 'attachment_filename'
                )
    return jsonify({"error": "Image not found"}), 404



def delete_user_images(username):
    result = mongo.db.images.delete_many({"username": username})
    return result.deleted_count
