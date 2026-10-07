import os
from pathlib import Path

from dotenv import load_dotenv

# اول .env کنار پروژه، بعد مسیر قدیمی C:\11\.env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv(r"C:\11\.env", override=False)

TOKENS = [
    os.getenv("BOT_TOKEN_1"),
    os.getenv("BOT_TOKEN_2"),
    os.getenv("BOT_TOKEN_3"),
]
TOKENS = [t for t in TOKENS if t]

ALLOWED_USER_IDS = {
    1635755123,
    7352264911,
    8613300692,
    8197645586,
    7908007061,
}

# 0 = بدون محدودیت (تا وقتی /off بزنی)
MAX_MESSAGES = 0

# 0 = بدون تاخیر؛ سرعت واقعی را فقط محدودیت خود تلگرام کنترل می‌کند
MESSAGE_DELAY = 0


print("Loaded tokens:", len(TOKENS), flush=True)
