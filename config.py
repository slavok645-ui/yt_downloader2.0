import os

BOT_TOKEN = ""
DOWNLOAD_DIR = "downloads"
DB_PATH = "data/history.db"

ADMIN_ID = 123456789


os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)