import os
import re
import random
import urllib.parse
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper

def fix_arabic_text(text):
    """تنظيف وتشكيل وعكس النص يدوياً لضمان ظهوره بشكل سليم 100%"""
    clean = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text).strip()
    reshaper = arabic_reshaper.ArabicReshaper({'delete_harakat': True, 'support_ligatures': True})
    reshaped_text = reshaper.reshape(clean)
    return reshaped_text[::-1] # عكس النص برمجياً

def download_file(url, target_path):
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_custom_ai_image(prompt, output_path):
    """توليد الصورة بالذكاء الاصطناعي وقص العلامة المائية برمجياً لتجنب الدفع"""
    print(f"جاري توليد الصورة المخصصة: {output_path}...")
    safe_prompt = urllib.parse.quote(prompt)
    
    # طلب الصورة بارتفاع 1160 بكسل (لترك مساحة للعلامة المائية بالأسفل)
    # استخدام نموذج flux المجاني والسريع
    seed = random.randint(1, 100000)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1160&model=flux&seed={seed}"
    
    try:
        download_file(url, "temp_ai.jpg")
        
        # فتح الصورة وقص الجزء السفلي (80 بكسل) لإزالة العلامة المائية
        img = Image.open("temp_ai.jpg").convert("RGB")
        # الإحداثيات: (اليسار، الأعلى، اليمين، الأسفل)
        cropped_img = img.crop((0, 0, 1920, 1080))
        cropped_img.save(output_path, quality=100)
        
        print(f"✅ تم توليد وقص الصورة بنجاح وبدون علامة مائية: {output_path}")
        return True
    except Exception as e:
        print(f"خطأ أثناء توليد الصورة: {e}")
        # صورة احتياطية في أسوأ الحالات
        Image.new("RGB", (1920, 1080), (30, 40, 30)).save(output_path)
        return False

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())

    # 1. جلب بيانات السورة
    meta = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    raw_name = meta["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل التلاوة
    audio_file = "audio.mp3"
    print("جاري تحميل الصوت...")
    download_file(f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3", audio_file)

    # 3. تحميل الخط
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. توليد خلفية الفيديو (الغرفة التراثية كما طلبتها)
    bg_prompt = (
        "Cinematic ultra detailed shot of cozy traditional Islamic room, open Holy Quran on wooden rehal stand, "
        "vintage wooden radio, warm lantern on Persian carpet, open wooden mashrabiya window overlooking minaret at sunset, 8k, photorealistic"
    )
    generate_custom_ai_image(bg_prompt, "bg_video.jpg")

    # 5. توليد خلفية الغلاف (زخارف إسلامية والمنشاوي)
    thumb_prompt = (
        "Luxury Islamic background, dark green and gold arabesque patterns, "
        "ornate golden calligraphy frame banner in center right with empty space, "
        "vintage portrait of Egyptian Quran reciter Sheikh Al-Minshawi on the left wearing white turban, 8k, masterpiece"
    )
    generate_custom_ai_image(thumb_prompt, "thumb_raw.jpg")

    # 6. الكتابة على الغلاف بالنص السليم 100%
    thumb_img = Image.open("thumb_raw.jpg").convert("RGBA")
    # تظليل خفيف جداً لبروز النص
    overlay = Image.new("RGBA", thumb_img.size, (0, 0, 0, 90))
    thumb_img = Image.alpha_composite(thumb_img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 160)
    sub_font = ImageFont.truetype(font_file, 70)

    # حساب المنتصف لكتابة اسم السورة
    bbox = draw.textbbox((0, 0), surah_title, font=title_font, direction='ltr')
    tw = bbox[2] - bbox[0]
    tx = (1920 - tw) // 2
    ty = 400

    draw.text((tx + 5, ty + 5), surah_title, font=title_font, fill=(0, 0, 0), direction='ltr')
    draw.text((tx, ty), surah_title, font=title_font, fill=(245, 215, 110), direction='ltr')

    sheikh_text = fix_arabic_text("الشيخ محمد صديق المنشاوي")
    s_bbox = draw.textbbox((0, 0), sheikh_text, font=sub_font, direction='ltr')
    s_tw = s_bbox[2] - s_bbox[0]
    s_tx = (1920 - s_tw) // 2
    
    draw.text((s_tx + 3, 650 + 3), sheikh_text, font=sub_font, fill=(0, 0, 0), direction='ltr')
    draw.text((s_tx, 650), sheikh_text, font=sub_font, fill=(255, 255, 255), direction='ltr')

    thumb_img.save("thumbnail_final.jpg", quality=100)
    print("✅ تم تصميم الغلاف بنجاح.")

    # 7. دمج الفيديو
    print("جاري دمج الفيديو...")
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
    print("🚀 تم إنتاج الفيديو النهائي بالذكاء الاصطناعي بنجاح!")

if __name__ == "__main__":
    main()
