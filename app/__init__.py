import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  

# Create the Flask application instance
app = Flask(__name__)

# Configure app instance
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# Set static folder path
static_folder_path = os.path.join(app.root_path, 'static')
app.static_folder = static_folder_path

# Create SQLite instance
db = SQLAlchemy(app)
from app.models import Document
# Create the context
with app.app_context():
    # Create the database tables
    db.create_all()

# Register blueprints here
from app.home.routes import home_route
from app.upload.routes import upload_route
app.register_blueprint(home_route)
app.register_blueprint(upload_route)
