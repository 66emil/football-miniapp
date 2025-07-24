import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}

if not BOT_TOKEN or not ADMIN_IDS:
    raise RuntimeError("BOT_TOKEN и ADMIN_IDS обязаны быть в .env")

