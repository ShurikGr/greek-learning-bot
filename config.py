import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")

# Admin whitelist (Telegram usernames without @)
ADMIN_USERNAMES = os.getenv('ADMIN_USERNAME', '').split(',')

# Database
DATABASE_PATH = "database/words.db"

# Default settings
DEFAULT_QUESTIONS_PER_SESSION = 5
DEFAULT_SESSION_INTERVAL_MINUTES = 15
DEFAULT_GROUP_POST_INTERVAL_MINUTES = 30

# Quiz settings
MIN_ANSWERS_FOR_DIFFICULTY_CALC = 3
DIFFICULTY_MULTIPLIER_LOW = 0.5
DIFFICULTY_MULTIPLIER_NORMAL = 1.0
DIFFICULTY_MULTIPLIER_HIGH = 2.0
SUCCESS_RATE_THRESHOLD_HIGH = 0.9
SUCCESS_RATE_THRESHOLD_LOW = 0.7
