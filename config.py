from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("bot_token")
ADMIN_TG_ID = os.getenv("admin_tg_id")