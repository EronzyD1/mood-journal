import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev")
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")

    # Hugging Face
    HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    HF_MODEL = os.getenv("HUGGINGFACE_MODEL", "j-hartmann/emotion-english-distilroberta-base")

    # Flutterwave
    FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")
    FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
    FLW_WEBHOOK_SECRET = os.getenv("FLW_WEBHOOK_SECRET", "")

    SUBSCRIPTION_AMOUNT = int(os.getenv("SUBSCRIPTION_AMOUNT", 2000))
    SUBSCRIPTION_CURRENCY = os.getenv("SUBSCRIPTION_CURRENCY", "NGN")
    SUBSCRIPTION_DURATION_DAYS = int(os.getenv("SUBSCRIPTION_DURATION_DAYS", 365))

    PERMANENT_SESSION_LIFETIME = timedelta(days=365*5)
