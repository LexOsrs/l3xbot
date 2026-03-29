import os
# Configuration file for l3xbot

TOKEN = os.getenv("BOT_TOKEN")
BINGO_API_URL = os.getenv("BINGO_API_URL", "http://localhost:5209/api/bingo")
BINGO_MOD_CHANNEL_ID = int(os.getenv("BINGO_MOD_CHANNEL_ID", "0"))
