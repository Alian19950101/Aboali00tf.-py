import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# إعدادات أساسية
TOKEN = '7844256099:AAE2NQSVBU_VaYT_4RdZxFocLZLv_jfqVrs'
PORT = 10000
COOKIES_FILE = 'cookies.txt'

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل رابط فيديو لتحميله")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = update.message.text
        ydl_opts = {'quiet': True, 'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None}
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
            
        buttons = [[InlineKeyboardButton(f"{f.get('height', '')}p", callback_data=f['format_id'])] for f in formats[:5]]
        await update.message.reply_text("اختر الجودة:", reply_markup=InlineKeyboardMarkup(buttons))
    
    except Exception as e:
        await update.message.reply_text(f"خطأ: {str(e)}")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("جاري التحميل...")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))
    app.add_handler(CallbackQueryHandler(download))
    
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        key='private.key',
        cert='cert.pem',
        webhook_url='https://aboali00tf-py.onrender.com/webhook'
    )

if __name__ == '__main__':
    main()
