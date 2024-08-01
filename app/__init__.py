from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS  # Import CORS
import os
from dotenv import load_dotenv

mongo = PyMongo()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    CORS(app)
    # Load environment variables from .env file
    load_dotenv()
    
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    
    mongo.init_app(app)
    bcrypt.init_app(app)

    
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    return app
