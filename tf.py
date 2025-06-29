import os
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from yt_dlp import YoutubeDL

# إعدادات البوت
TOKEN = '7844256099:AAE2NQSVBU_VaYT_4RdZxFocLZLv_jfqVrs'
WEBHOOK_URL = 'https://aboali00tf-py.onrender.com/webhook'
PORT = 10000
COOKIES_FILE = 'cookies.txt'
MAX_FILE_SIZE = 2000 * 1024 * 1024

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# باقي الكود كما هو بدون تغيير ...
# [يجب أن يحتوي هنا على جميع الدوال الأخرى الموجودة في الكود السابق]
# ...

def main():
    application = Application.builder().token(TOKEN).build()
    
    # تسجيل المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
    application.add_handler(CallbackQueryHandler(download_video))
    
    logger.info(f"بدء التشغيل على المنفذ {PORT}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        cert=None,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
