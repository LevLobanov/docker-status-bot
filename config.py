from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("bot_token")
ADMIN_TG_ID = [int(id) for id in str(os.getenv("admin_tg_id")).split(',')]
