import os
import glob
import subprocess
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

# 1. إعداد مسارات الملفات الأساسية
font_path = "Amiri-Bold.ttf" 
base_image = "base_room_empty.jpg"

# التأكد من وجود الخط والصورة الأساسية قبل البدء
if not os.path.exists(font_path) or not os.path.exists(base_image):
    print("خطأ: تأكد من رفع ملف الخط Amiri-Bold.ttf والصورة الأساسية base_room_empty.jpg")
    exit(1)

# البحث عن جميع ملفات الصوت في المجلد
audio_files = glob.glob("*.mp3")

if not audio_files:
    print("لم يتم العثور على ملفات صوت بصيغة mp3.")
    exit(0)

# 2. حلقة تكرارية لمعالجة كل ملف صوتي تلقائياً
for audio_file in audio_files:
    # استخراج اسم السورة من اسم الملف بدون الامتداد
    surah_name = os.path.splitext(audio_file)[0]
    output_image = f"cover_{surah_name}.jpg"
    final_video = f"video_{surah_name}.mp4"
    
    print(f"جاري معالجة: {surah_name}...")

    # 3. ضبط النص العربي لمنع ظهوره مقلوباً أو متقطعاً
    text_to_write = f"الشيخ محمد صديق المنشاوي\n{surah_name}"
    reshaped_text = arabic_reshaper.reshape(text_to_write)
    bidi_text = get_display(reshaped_text)

    # 4. الكتابة على الصورة
    image = Image.open(base_image)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, 80)
    
    # وضع النص في منتصف الصورة تماماً
    draw.multiline_text((image.width/2, image.height/2), bidi_text, font=font, fill="#F5DEB3", anchor="mm", align="center")
    image.save(output_image)

    # 5. دمج الصوت والصورة وإضافة تأثير التلفزيون القديم باستخدام FFmpeg
    ffmpeg_cmd = [
        "ffmpeg", "-loop", "1", "-i", output_image, "-i", audio_file,
        "-vf", "noise=alls=15:allf=t+u,eq=contrast=1.1:brightness=-0.05:saturation=0.7",
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest", "-y", final_video
    ]
    
    subprocess.run(ffmpeg_cmd)
    print(f"تم بنجاح إنشاء فيديو: {final_video}\n")
