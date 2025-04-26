import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot API Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "info_bot_db")

# Collection names
VITAMINS_COLLECTION = "vitamins"
PLANTS_COLLECTION = "plants"
USERS_COLLECTION = "users"
FEEDBACK_COLLECTION = "feedback"

CHUTES_API_TOKEN = os.getenv('CHUTES_API_TOKEN')

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True) 