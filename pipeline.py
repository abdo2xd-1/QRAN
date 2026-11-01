import os
import re
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # إزالة تشكيل المصحف لتفادي انقلاب أو انفصال الحروف
    clean_text = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]', '', text)
    # اتصال الحروف العربية وضبط اتجاه القراءة من اليمين لليسار
    reshaped = arabic_reshaper.reshape(clean_text)
    return get_display(reshaped)

def generate_video_bg():
    """توليد خلفية تراثية دافئة للفيديو برمجياً بالكامل"""
    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), color=(24, 18, 12))
    draw = ImageDraw.Draw(img)

    # تدرج لوني دافئ
    for y in range(height):
        r = int(24 + (y / height) * 20)
        g = int(18 + (y / height) * 10)
        b = int(12 + (y / height) * 5)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # إطار داخلي ذهبي
    border_margin = 40
    draw.rectangle(
        [(border_margin, border_margin), (width - border_margin, height - border_margin)],
        outline=(140, 105, 55), width=3
    )
    draw.rectangle(
        [(border_margin + 10, border_margin + 10), (width - border_margin - 10, height - border_margin - 10)],
        outline=(90, 70, 35), width=1
    )

    # زخارف الأركان
    corner_size = 60
    for cx, cy, x_sign, y_sign in [
        (border_margin, border_margin, 1, 1),
        (width - border_margin, border_margin, -1, 1),
        (border_margin, height - border_margin, 1, -1),
        (width - border_margin, height - border_margin, -1, -1)
    ]:
        draw.line([(cx, cy), (cx + x_sign * corner_size, cy)], fill=(140, 105, 55), width=4)
        draw.line([(cx, cy), (cx, cy + y_sign * corner_size)], fill=(140, 105, 55), width=4)

    # كتابة كلمة آيات قرآنية
    font_file = "Amiri-Bold.ttf"
    if os.path.exists(font_file):
        small_font = ImageFont.truetype(font_file, 40)
        tag_text = fix_arabic_text("آيات قرآنية")
        draw.text((80, 80), tag_text, font=small_font, fill=(180, 150, 100))

    img.save("bg_video.jpg", quality=95)
    print("✅ تم توليد خلفية الفيديو بنجاح.")

def generate_thumbnail(surah_title):
    """توليد الصورة المصغرة (الغلاف) وتنسيق النصوص تلقائياً"""
    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), color=(15, 25, 18))
    draw = ImageDraw.Draw(img)

    # تدرج لوني إسلامي هادئ
    for y in range(height):
        r = int(12 + (y / height) * 15)
        g = int(22 + (y / height) * 12)
        b = int(14 + (y / height) * 8)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # إطار خارجي مزدوج
    draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(197, 160, 89), width=5)
    draw.rectangle([(65, 65), (width - 65, height - 65)], outline=(140, 110, 50), width=2)

    font_file = "Amiri-Bold.ttf"
    if os.path.exists(font_file):
        sub_font = ImageFont.truetype(font_file, 55)
        large_font = ImageFont.truetype(font_file, 140)
        reader_font = ImageFont.truetype(font_file, 70)

        # "ماتيسر من"
        intro_text = fix_arabic_text("ماتيسر من")
        draw.text((1150, 200), intro_text, font=sub_font, fill=(240, 240, 240))

        # اسم السورة
        draw.text((950, 320), surah_title, font=large_font, fill=(245, 215, 110))

        # "بدون صدى صوت"
        spec_text = fix_arabic_text("بدون صدى صوت")
        draw.rectangle([(1100, 550), (1500, 630)], fill=(40, 30, 20), outline=(197, 160, 89), width=2)
        draw.text((1150, 560), spec_text, font=ImageFont.truetype(font_file, 40), fill=(240, 240, 240))

        # اسم القارئ
        sheikh_intro = fix_arabic_text("الشيخ")
        sheikh_name = fix_arabic_text("محمد صديق المنشاوي")
        sheikh_sub = fix_arabic_text("رحمه الله")

        draw.text((1250, 700), sheikh_intro, font=sub_font, fill=(180, 180, 180))
        draw.text((1050, 780), sheikh_name, font=reader_font, fill=(255, 255, 255))
        draw.text((1220, 880), sheikh_sub, font=sub_font, fill=(180, 180, 180))

        # كادر جانبي للتلاوة
        draw.rectangle([(150, 200), (550, 880)], outline=(197, 160, 89), width=2)
        placeholder_text = fix_arabic_text("تلاوة خاشعة")
        draw.text((250, 500), placeholder_text, font=sub_font, fill=(197, 160, 89))

    img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم توليد الغلاف الرقمي بنجاح.")

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())

    # 1. جلب بيانات السورة
    res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    raw_name = res["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    # حفظ النصوص
    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت الشيخ محمد صديق المنشاوي.")

    # 2. تحميل تلاوة الشيخ المنشاوي
    audio_file = "audio.mp3"
    audio_url = f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3"
    with requests.get(audio_url, stream=True) as r:
        with open(audio_file, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

    # 3. تحميل الخط العربي
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf"
        with requests.get(font_url) as r:
            with open(font_file, 'wb') as f:
                f.write(r.content)

    # 4. توليد الصور تلقائياً
    generate_video_bg()
    generate_thumbnail(surah_title)

    # 5. الدمج بـ FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "bg_video.jpg",
        "-i", audio_file,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080",
        "-shortest",
        "output.mp4"
    ]
    subprocess.run(cmd, check=True)
    print("🚀 تم إنتاج الفيديو والصورة بنجاح وبدون أي أخطاء!")

if __name__ == "__main__":
    main()
