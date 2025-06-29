#!/bin/bash

# إنشاء بيئة افتراضية
python3 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt

# تحميل ملفات الكوكيز (إذا وجدت)
if [ ! -f cookies.txt ]; then
    echo "ملاحظة: قم بإنشاء ملف cookies.txt لتتمكن من تنزيل فيديوهات تويتر"
fi

# تشغيل البوت
python tf.py
