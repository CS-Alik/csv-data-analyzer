import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    # Your exact Render database URL
    SQLALCHEMY_DATABASE_URI = "postgresql://csv_db_h4rx_user:ur7VZ3uF87dmVCoe7scOhqKaZSapRNBj@dpg-d985nbeq1p3s73fruk9g-a/csv_db_h4rx"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"csv"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 50)) * 1024 * 1024

    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"
