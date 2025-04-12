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