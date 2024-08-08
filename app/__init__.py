from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from dotenv import load_dotenv

mongo = PyMongo()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    load_dotenv()

    mongo_uri = os.getenv('MONGO_URI')
    jwt_secret_key = os.getenv('JWT_SECRET_KEY')
    frontend_url = os.getenv('FRONTEND_URL')
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    s3_bucket_name = os.getenv('S3_BUCKET_NAME')
    
    if not all([mongo_uri, jwt_secret_key, frontend_url, aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket_name]):
        raise ValueError("One or more environment variables are missing")
    
    app.config['MONGO_URI'] = mongo_uri
    app.config['JWT_SECRET_KEY'] = jwt_secret_key
    app.config['FRONTEND_URL'] = frontend_url
    app.config['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    app.config['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
    app.config['AWS_REGION'] = aws_region
    app.config['S3_BUCKET_NAME'] = s3_bucket_name
    
    # Debug prints
    print(f"S3_BUCKET_NAME: {app.config.get('S3_BUCKET_NAME')}")

    CORS(app, resources={r"/*": {"origins": "*"}})

    mongo.init_app(app)
    bcrypt.init_app(app)

    # Ensure the extensions are registered
    app.extensions['pymongo'] = mongo
    app.extensions['bcrypt'] = bcrypt
    
    from app.routes.client_routes import client_bp
    from app.routes.image_routes import image_bp
    from app.routes.matching_routes import matching_bp
    from app.routes.user_routes import user_bp

    app.register_blueprint(client_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(user_bp)
    
    return app
