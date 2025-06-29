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

# إعدادات البوت - يمكن تعديلها
TOKEN = os.getenv('TELEGRAM_TOKEN', '7844256099:AAE2NQSVBU_VaYT_4RdZxFocLZLv_jfqVrs')
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://yourdomain.com/webhook')
COOKIES_FILE = os.getenv('COOKIES_FILE', 'cookies.txt')
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB كحد أقصى

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالة المحادثة
CHOOSING_QUALITY, DOWNLOADING = range(2)

def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المسموح بها"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **مرحباً في بوت تنزيل الفيديو الاحترافي!**\n\n"
        "أرسل رابط الفيديو (من يوتيوب، تويتر، إنستجرام، تيك توك، إلخ) وسأقوم بتنزيله لك بالجودة التي تختارها."
    )

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data['url'] = url
    user_id = update.message.from_user.id
    
    try:
        # إعداد خيارات استخراج المعلومات
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None
        }
        
        # استخراج معلومات الفيديو
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            title = clean_filename(info.get('title', 'video'))
            context.user_data['title'] = title
        
        # فلترة التنسيقات المتاحة (فيديو فقط)
        video_formats = {}
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('filesize') and f.get('filesize') < MAX_FILE_SIZE:
                res = f.get('format_note', '') or f"{f.get('height')}p"
                if res and res not in video_formats:
                    video_formats[res] = f['format_id']
        
        # إذا لم نجد أي تنسيقات فيديو
        if not video_formats:
            await update.message.reply_text("❌ لم يتم العثور على تنسيقات فيديو متاحة أو حجم الفيديو كبير جداً (>2GB).")
            return -1
        
        # إنشاء أزرار الدقة
        keyboard = [
            [InlineKeyboardButton(q, callback_data=fid)] 
            for q, fid in video_formats.items()
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📹 **{title}**\n\nاختر جودة الفيديو:",
            reply_markup=reply_markup
        )
        return CHOOSING_QUALITY

    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة الرابط. تأكد من صحته وحاول مرة أخرى.")
        return -1

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_id = query.data
    url = context.user_data['url']
    title = context.user_data['title']
    user_id = query.from_user.id
    
    await query.edit_message_text(f"⏳ جار التحميل... الرجاء الانتظار قد تستغرق العملية بضع دقائق.")
    
    try:
        # إعداد خيارات التنزيل
        ydl_opts = {
            'format': format_id,
            'outtmpl': f"{title}.%(ext)s",
            'merge_output_format': 'mp4',
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            'progress_hooks': [lambda d: logger.info(f"Progress: {d.get('_percent_str', '')}")],
            'quiet': True
        }
        
        # تنزيل الفيديو
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # إرسال الفيديو
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_video")
        
        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_file,
                caption=f"✅ {title}",
                supports_streaming=True,
                read_timeout=60,
                write_timeout=60,
                connect_timeout=60
            )
        
        # حذف الملف المؤقت
        os.remove(filename)
        logger.info(f"تم إرسال الفيديو بنجاح للمستخدم {user_id}")
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text("❌ فشل التحميل. قد يكون الفيديو محمياً أو الدقة غير متوفرة.")
        if os.path.exists(filename):
            os.remove(filename)

    return -1

def main():
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # تسجيل المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
    application.add_handler(CallbackQueryHandler(download_video))
    
    # التحقق من وجود ملف الكوكيز
    if not os.path.exists(COOKIES_FILE):
        logger.warning(f"ملف الكوكيز {COOKIES_FILE} غير موجود. قد لا تعمل تنزيلات تويتر.")
    
    # إعداد ويب هوك
    logger.info(f"Starting bot in webhook mode on port {PORT}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        cert=None,
    )

if __name__ == "__main__":
    main()
