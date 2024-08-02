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
    
    if not all([mongo_uri, jwt_secret_key, frontend_url]):
        raise ValueError("One or more environment variables are missing")

    app.config['MONGO_URI'] = mongo_uri
    app.config['JWT_SECRET_KEY'] = jwt_secret_key
    app.config['FRONTEND_URL'] = frontend_url

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
