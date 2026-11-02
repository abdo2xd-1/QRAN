import os
import re
import urllib.parse
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # تنظيف وتشكيل قياسي 100% بدون عكس يدوي عشان ميضربش في السيرفر
    clean = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text).strip()
    reshaper = arabic_reshaper.ArabicReshaper({'delete_harakat': True})
    return get_display(reshaper.reshape(clean))

def download_file(url, target_path):
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_image_free(prompt, output_path):
    """توليد مجاني للصور وقص العلامة المائية برمجياً"""
    print(f"جاري توليد الصورة بالذكاء الاصطناعي: {output_path}...")
    safe_prompt = urllib.parse.quote(prompt)
    
    # نطلب الصورة بدون أمر إزالة العلامة المائية عشان نتجنب الدفع (خطأ 402)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&model=flux"
    
    try:
        download_file(url, "temp.jpg")
        img = Image.open("temp.jpg").convert("RGB")
        
        # قص 45 بيكسل من الأسفل لإزالة العلامة المائية (pollinations.ai) نهائياً
        width, height = img.size
        cropped_img = img.crop((0, 0, width, height - 45))
        
        # تكبير الصورة مرة أخرى لتملا الشاشة بالكامل 1920x1080
        final_img = cropped_img.resize((1920, 1080), Image.Resampling.LANCZOS)
        final_img.save(output_path, quality=100)
        print(f"✅ تم التوليد وإزالة العلامة المائية بنجاح: {output_path}")
    except Exception as e:
        print(f"خطأ في التوليد: {e}")
        Image.new("RGB", (1920, 1080), (28, 20, 14)).save(output_path)

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())

    # 1. بيانات السورة
    meta = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    raw_name = meta["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل الصوت
    audio_file = "audio.mp3"
    print("جاري تحميل الصوت...")
    download_file(f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3", audio_file)

    # 3. تحميل الخط
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. توليد الخلفيات المخصصة
    bg_prompt = "Cinematic ultra detailed shot of cozy traditional Islamic room, open Holy Quran on wooden rehal stand, vintage wooden radio, warm lantern on Persian carpet, open wooden mashrabiya window overlooking minaret at sunset, 8k, photorealistic"
    generate_image_free(bg_prompt, "bg_video.jpg")

    thumb_prompt = "Luxury Islamic background, dark green and gold arabesque patterns, ornate golden calligraphy frame banner in center right with empty space, vintage portrait of Egyptian Quran reciter Sheikh Al-Minshawi on the left wearing white turban, 8k, masterpiece"
    generate_image_free(thumb_prompt, "thumb_raw.jpg")

    # 5. الكتابة والرسم
    thumb_img = Image.open("thumb_raw.jpg").convert("RGBA")
    overlay = Image.new("RGBA", thumb_img.size, (0, 0, 0, 110))
    thumb_img = Image.alpha_composite(thumb_img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 160)
    sub_font = ImageFont.truetype(font_file, 70)

    # كتابة السورة
    bbox = draw.textbbox((0, 0), surah_title, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (1920 - tw) // 2
    ty = 400
    draw.text((tx + 5, ty + 5), surah_title, font=title_font, fill=(0, 0, 0))
    draw.text((tx, ty), surah_title, font=title_font, fill=(245, 215, 110))

    # كتابة اسم الشيخ
    sheikh_text = fix_arabic_text("الشيخ محمد صديق المنشاوي")
    s_bbox = draw.textbbox((0, 0), sheikh_text, font=sub_font)
    s_tw = s_bbox[2] - s_bbox[0]
    s_tx = (1920 - s_tw) // 2
    draw.text((s_tx + 3, 650 + 3), sheikh_text, font=sub_font, fill=(0, 0, 0))
    draw.text((s_tx, 650), sheikh_text, font=sub_font, fill=(255, 255, 255))

    thumb_img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم تصميم الغلاف بنجاح!")

    # 6. دمج الفيديو
    print("جاري التصدير...")
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", "bg_video.jpg", "-i", audio_file,
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-vf", "scale=1920:1080", "-shortest", "output.mp4"
    ]
    subprocess.run(cmd, check=True)
    print("🚀 تمت العملية بنجاح!")

if __name__ == "__main__":
    main()
