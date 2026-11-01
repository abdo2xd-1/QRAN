import os
import re
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # إزالة تشكيل المصحف لتفادي انقلاب وانفصال الحروف
    clean_text = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]', '', text)
    # تشكيل واتصال الحروف وضبط اتجاه القراءة من اليمين لليسار
    reshaped = arabic_reshaper.reshape(clean_text)
    return get_display(reshaped)

def get_existing_file(base_name):
    # البحث عن الملف بكل الامتدادات الممكنة سواء حروف صغيرة أو كبيرة
    for ext in ['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG']:
        filename = f"{base_name}.{ext}"
        if os.path.exists(filename):
            return filename
    return None

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())

    # 1. جلب بيانات السورة
    res = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    raw_name = res["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    # حفظ نصوص العنوان والوصف
    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت الشيخ محمد صديق المنشاوي.")

    # 2. تحميل ملف الصوت للسورة
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

    # 4. توليد الصورة المصغرة (Thumbnail)
    thumb_template = get_existing_file("thumb_template")
    if thumb_template:
        thumb_img = Image.open(thumb_template).convert("RGBA").resize((1920, 1080))
    else:
        thumb_img = Image.new("RGBA", (1920, 1080), (18, 25, 20, 255))

    draw = ImageDraw.Draw(thumb_img)
    font = ImageFont.truetype(font_file, 130)

    # محاذاة النص في مكان الإطار
    bbox = draw.textbbox((0, 0), surah_title, font=font)
    tw = bbox[2] - bbox[0]
    tx = int(1920 * 0.58) - (tw // 2)
    ty = int(1080 * 0.38)

    # رسم ظل أسود ثم النص الذهبي
    draw.text((tx + 3, ty + 3), surah_title, font=font, fill=(0, 0, 0, 220))
    draw.text((tx, ty), surah_title, font=font, fill=(245, 215, 110))

    thumb_final = "thumbnail_final.jpg"
    thumb_img.convert("RGB").save(thumb_final, quality=95)

    # 5. تحديد خلفية الفيديو
    video_bg = get_existing_file("bg_video")
    if not video_bg:
        video_bg = thumb_final

    # 6. دمج الصوت مع الصورة عبر FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", video_bg,
        "-i", audio_file,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-shortest",
        "output.mp4"
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
