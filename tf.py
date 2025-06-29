import os
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
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
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB كحد أقصى

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
CHOOSING_QUALITY, DOWNLOADING = range(2)

def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **مرحباً في بوت تنزيل الفيديو الاحترافي!**\n\n"
        "أرسل رابط الفيديو (من يوتيوب، تويتر، إنستجرام، تيك توك، إلخ) وسأقوم بتنزيله لك بالجودة التي تختارها."
    )

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data['url'] = url
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            title = clean_filename(info.get('title', 'video'))
            context.user_data['title'] = title
        
        video_formats = {}
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('filesize', 0) < MAX_FILE_SIZE:
                res = f.get('format_note', '') or f"{f.get('height')}p"
                if res: video_formats[res] = f['format_id']
        
        if not video_formats:
            await update.message.reply_text("❌ لم يتم العثور على تنسيقات فيديو متاحة")
            return -1
        
        keyboard = [[InlineKeyboardButton(q, callback_data=fid)] for q, fid in video_formats.items()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📹 **{title}**\n\nاختر جودة الفيديو:",
            reply_markup=reply_markup
        )
        return CHOOSING_QUALITY

    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة الرابط")
        return -1

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_id = query.data
    url = context.user_data['url']
    title = context.user_data['title']
    
    await query.edit_message_text("⏳ جار التحميل... الرجاء الانتظار")
    
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': f"{title}.%(ext)s",
            'merge_output_format': 'mp4',
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            'quiet': True
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_video")
        
        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_file,
                caption=f"✅ {title}",
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=120
            )
        
        os.remove(filename)
        logger.info("تم إرسال الفيديو بنجاح")
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text("❌ فشل التحميل")
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

    return -1

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
app.add_handler(CallbackQueryHandler(download_video))

def main():
    if not os.path.exists(COOKIES_FILE):
        logger.warning("ملف الكوكيز غير موجود")
    
    logger.info(f"بدء التشغيل على المنفذ {PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        cert=None
    )

if __name__ == '__main__':
    main()
