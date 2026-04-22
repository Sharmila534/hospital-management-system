import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/hospital_db')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv("DEBUG", str(FLASK_ENV == 'development')) == "True"

