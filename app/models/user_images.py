from flask import current_app, send_file, jsonify
from bson import ObjectId
import io

def get_mongo():
    return current_app.extensions['pymongo']

def update_user_images(username, image_type, file):
    mongo = get_mongo()
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

def get_user_image_collection(username):
    mongo = get_mongo()
    return mongo.db.images.find_one({"username": username})

def get_image(username, image_type):
    mongo = get_mongo()
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
    mongo = get_mongo()
    result = mongo.db.images.delete_many({"username": username})
    return result.deleted_count
