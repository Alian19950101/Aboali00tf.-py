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

# ======= إعدادات البوت =======
TOKEN = '7844256099:AAE2NQSVBU_VaYT_4RdZxFocLZLv_jfqVrs'
WEBHOOK_URL = 'https://aboali00tf-py.onrender.com/webhook'
PORT = 10000  # المنفذ الإلزامي لـ Render
COOKIES_FILE = 'cookies.txt'
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB

# ======= إعداد التسجيل =======
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======= دوال المساعدة =======
def clean_filename(filename):
    """إزالة الأحرف غير المسموحة في أسماء الملفات"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# ======= معالجات الأوامر =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **مرحباً في بوت تنزيل الفيديو الاحترافي!**\n\n"
        "أرسل لي رابط الفيديو من أي منصة وسأساعدك في تحميله بأفضل جودة متاحة."
    )

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data['url'] = url
    
    try:
        # استخراج معلومات الفيديو
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

        # فلترة التنسيقات المتاحة
        video_formats = {}
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('filesize', 0) < MAX_FILE_SIZE:
                res = f.get('format_note', '') or f"{f.get('height')}p"
                if res: video_formats[res] = f['format_id']

        if not video_formats:
            await update.message.reply_text("⚠️ لم أجد تنسيقات فيديو متاحة أو الملف كبير جداً")
            return

        # إنشاء أزرار الاختيار
        keyboard = [
            [InlineKeyboardButton(quality, callback_data=fid)]
            for quality, fid in video_formats.items()
        ]
        
        await update.message.reply_text(
            f"🎬 **{title}**\n\nاختر جودة التحميل:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"خطأ في معالجة الرابط: {e}")
        await update.message.reply_text("❌ حدث خطأ! تأكد من صحة الرابط وحاول مرة أخرى")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_id = query.data
    url = context.user_data['url']
    title = context.user_data['title']
    
    await query.edit_message_text("⏳ جاري التحميل، قد يستغرق عدة دقائق...")

    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': f'{title}.%(ext)s',
            'merge_output_format': 'mp4',
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            'quiet': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await context.bot.send_chat_action(
            chat_id=query.message.chat_id,
            action="upload_video"
        )

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_file,
                caption=f"✅ {title}",
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=300
            )

        os.remove(filename)
        logger.info("تم إرسال الفيديو بنجاح")

    except Exception as e:
        logger.error(f"خطأ في التحميل: {e}")
        await query.edit_message_text("❌ فشل التحميل! قد تكون الجودة غير متاحة")
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

# ======= التشغيل الرئيسي =======
def main():
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()

    # تسجيل المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
    application.add_handler(CallbackQueryHandler(download_video))

    # التحقق من ملف الكوكيز
    if not os.path.exists(COOKIES_FILE):
        logger.warning("ملف الكوكيز غير موجود - تنزيل تويتر قد لا يعمل")

    # بدء التشغيل
    logger.info(f"جاري التشغيل على المنفذ {PORT}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        cert=None,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
