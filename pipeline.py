import os
import re
import urllib.parse
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # إزالة تشكيل المصحف لضمان اتصال الحروف وعدم قلبها
    clean_text = re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]', '', text)
    reshaped = arabic_reshaper.reshape(clean_text)
    return get_display(reshaped)

def download_file(url, target_path):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, stream=True, timeout=60)
    response.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_ai_image(prompt, output_filename):
    """توليد صورة واقعية فائقة الجودة عبر AI Image Generation API"""
    encoded_prompt = urllib.parse.quote(prompt)
    # رابط API مباشر لتوليد صور بدقة 1920x1080 وبجودة سينمائية
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed=42"
    print(f"جاري توليد الصورة عبر الذكاء الاصطناعي: {output_filename}...")
    download_file(api_url, output_filename)
    print(f"✅ تم تحميل وتوليد {output_filename}")

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())

    # 1. جلب اسم وبيانات السورة
    meta_url = f"https://api.alquran.cloud/v1/surah/{surah_num}"
    res = requests.get(meta_url).json()
    raw_name = res["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    print(f"السورة: {raw_name}")

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل تلاوة المنشاوي
    audio_file = "audio.mp3"
    audio_url = f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3"
    print("تحميل الصوت...")
    download_file(audio_url, audio_file)

    # 3. تحميل الخط العربي
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # -------------------------------------------------------------------------
    # 4. توليد خلفية الفيديو التراثية (نفس المشهد: غرفة تراثية، مصحف، راديو، شباك)
    # -------------------------------------------------------------------------
    video_prompt = (
        "Cinematic cozy traditional islamic heritage room, an open Quran on a wooden stand (rehal) "
        "placed on a vintage red Persian carpet, an antique vintage brown radio next to it, "
        "a traditional glowing lantern candle, an open ornate wooden mashrabiya window overlooking a minaret at sunset, "
        "warm cinematic lighting, photorealistic 8k, extremely detailed, historical aesthetic, no people"
    )
    generate_ai_image(video_prompt, "bg_video.jpg")

    # -------------------------------------------------------------------------
    # 5. توليد خلفية الغلاف (المصغرة) الإسلامية للشيخ المنشاوي
    # -------------------------------------------------------------------------
    thumb_prompt = (
        "Islamic youtube thumbnail background, luxury dark green and gold arabesque Islamic geometric patterns, "
        "ornate golden calligraphy frame banner in center right, empty space for text inside the frame, "
        "left side showing portrait of Sheikh Muhammad Siddiq Al-Minshawi with white amama and traditional azhar gown, "
        "golden ornate Quran on wooden rehal at bottom, professional graphic design, 8k resolution"
    )
    generate_ai_image(thumb_prompt, "thumb_raw.jpg")

    # كتابة اسم السورة داخل الإطار المخصص على الغلاف
    thumb_img = Image.open("thumb_raw.jpg").convert("RGB")
    draw = ImageDraw.Draw(thumb_img)
    font = ImageFont.truetype(font_file, 130)

    bbox = draw.textbbox((0, 0), surah_title, font=font)
    tw = bbox[2] - bbox[0]
    tx = int(1920 * 0.58) - (tw // 2)
    ty = int(1080 * 0.40)

    # رسم ظل أسود ثم النص بلون ذهبي
    draw.text((tx + 4, ty + 4), surah_title, font=font, fill=(0, 0, 0))
    draw.text((tx, ty), surah_title, font=font, fill=(245, 215, 110))

    thumb_img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم تجهيز الصورة المصغرة بنجاح.")

    # -------------------------------------------------------------------------
    # 6. دمج الصوت مع الفيديو بدقة 1080p
    # -------------------------------------------------------------------------
    print("جاري دمج الفيديو عبر FFmpeg...")
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
    print("🚀 تم إنتاج الفيديو والصورة بالذكاء الاصطناعي بنجاح وبأعلى جودة!")

if __name__ == "__main__":
    main()
