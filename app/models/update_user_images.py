import boto3
from flask import current_app, jsonify
from bson import ObjectId
from werkzeug.utils import secure_filename

def get_mongo():
    return current_app.extensions['pymongo']

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

def upload_to_s3(file, bucket_name, filename):
    s3_client = get_s3_client()
    s3_client.upload_fileobj(file, bucket_name, filename, ExtraArgs={"ContentType": file.content_type})
    return f"https://{bucket_name}.s3.{current_app.config['AWS_REGION']}.amazonaws.com/{filename}"

def update_user_images(username, image_type, file):
    mongo = get_mongo()
    image_collection = mongo.db.images
    filename = secure_filename(f"{username}_{image_type}.jpg")

    # Upload to S3
    s3_url = upload_to_s3(file, current_app.config['S3_BUCKET_NAME'], filename)

    image_data = {
        "filename": filename,
        "content_type": file.content_type,
        "url": s3_url,
        "type": image_type
    }

    user_images = image_collection.find_one({"username": username})

    if user_images and "images" in user_images:
        images = user_images["images"]

        image_found = False
        for img in images:
            if img["type"] == image_type:
                if "_id" not in img:
                    img["_id"] = str(ObjectId())  # Assign a new ObjectId if missing
                image_data["_id"] = img["_id"]
                image_collection.update_one(
                    {"username": username, "images._id": img["_id"]},
                    {"$set": {"images.$": image_data}}
                )
                image_found = True
                break

        if not image_found:
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
        new_user_images = {
            "username": username,
            "images": [image_data]
        }
        result = image_collection.insert_one(new_user_images)

        if result.inserted_id:
            return {"success": "Image collection updated successfully"}
        else:
            return {"error": "Failed to insert new image collection"}

def get_image(username, image_type):
    mongo = get_mongo()
    image_collection = mongo.db.images
    user_images = image_collection.find_one({"username": username})
    
    if user_images and "images" in user_images:
        for img in user_images["images"]:
            if img["type"] == image_type:
                return jsonify({"url": img["url"]}), 200

    return jsonify({"error": "Image not found"}), 404

def get_user_image_collection(username):
    mongo = get_mongo()
    print(f"Connecting to MongoDB: {mongo}")  # Debug connection info
    image_collection = mongo.db.images
    print(f"Querying for username: {username}")
    user_images = image_collection.find_one({"username": username})
    print(f"Retrieved user images: {user_images}")
    return user_images
