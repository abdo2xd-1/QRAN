import os
import re
import io
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from google import genai
from google.genai import types

def fix_arabic_text(text):
    """الطريقة القياسية المضمونة 100% لضبط النص العربي"""
    # تنظيف تشكيل المصحف والرموز المخفية
    clean = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text).strip()
    
    # ربط الحروف
    reshaper = arabic_reshaper.ArabicReshaper({
        'delete_harakat': True,
        'support_ligatures': True,
        'shift_harakat_position': False
    })
    reshaped_text = reshaper.reshape(clean)
    
    # ضبط الاتجاه
    return get_display(reshaped_text)

def download_file(url, target_path):
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_image_gemini(client, prompt, output_path):
    """توليد الصورة بدقة عالية باستخدام Imagen 3 من Google"""
    print(f"جاري توليد الصورة المخصصة عبر Gemini AI: {output_path}...")
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg",
                person_generation="ALLOW_ADULT"
            )
        )
        for generated_image in result.generated_images:
            img = Image.open(io.BytesIO(generated_image.image.image_bytes))
            # التأكد من الأبعاد وتعبئة الشاشة 1920x1080
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            img.save(output_path, quality=100)
            print(f"✅ تم التوليد بنجاح: {output_path}")
            return True
    except Exception as e:
        print(f"❌ خطأ في الاتصال بمحرك جيميني: {e}")
    
    print(f"⚠️ فشل توليد الصورة. سيتم إنشاء خلفية احتياطية مؤقتة.")
    Image.new("RGB", (1920, 1080), (28, 20, 14)).save(output_path)
    return False

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())
    api_key = os.environ.get("API_KEY", "").strip()

    if not api_key:
        raise ValueError("مفتاح API_KEY غير موجود! تأكد من إضافته في GitHub Secrets.")

    client = genai.Client(api_key=api_key)

    # 1. بيانات السورة
    meta = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    raw_name = meta["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل التلاوة
    audio_file = "audio.mp3"
    print("جاري تحميل التلاوة...")
    download_file(f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3", audio_file)

    # 3. تحميل الخط العربي الأصيل
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. تفاصيل ووصف صورة الفيديو (الغرفة التراثية الدقيقة)
    bg_prompt = (
        "Cinematic ultra detailed shot of a cozy traditional Islamic heritage room, "
        "an open Holy Quran resting on a carved wooden rehal stand, "
        "an antique vintage brown wooden radio, a warm glowing brass lantern placed on an authentic rich red Persian carpet, "
        "an open ornate wooden mashrabiya window overlooking a beautiful mosque minaret during a golden sunset, "
        "warm atmospheric lighting, 8k resolution, photorealistic, empty room, no text, no people."
    )
    generate_image_gemini(client, bg_prompt, "bg_video.jpg")

    # 5. تفاصيل ووصف صورة الغلاف (الشيخ المنشاوي والإطار الزخرفي)
    thumb_prompt = (
        "Luxury Islamic youtube thumbnail background, dark emerald green and shimmering gold arabesque geometric patterns, "
        "a large empty ornate golden calligraphy frame banner in the center right to leave space for typography, "
        "a vintage realistic portrait of the revered Egyptian Quran reciter Sheikh Muhammad Siddiq Al-Minshawi on the left side wearing his traditional white turban (amama) and Azhari gown, "
        "8k resolution, masterpiece, professional graphic design layout, absolutely no text written inside the image."
    )
    generate_image_gemini(client, thumb_prompt, "thumb_raw.jpg")

    # 6. كتابة النصوص العربية السليمة على الغلاف المولد
    thumb_img = Image.open("thumb_raw.jpg").convert("RGBA")
    
    # إضافة تظليل أسود شفاف (Opacity) بنسبة 40% لزيادة وضوح النص الذهبي وبروزه
    overlay = Image.new("RGBA", thumb_img.size, (0, 0, 0, 100))
    thumb_img = Image.alpha_composite(thumb_img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 160)
    sub_font = ImageFont.truetype(font_file, 70)

    # --- رسم اسم السورة ---
    bbox = draw.textbbox((0, 0), surah_title, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (1920 - tw) // 2
    ty = 400
    
    # ظل أسود عميق
    draw.text((tx + 6, ty + 6), surah_title, font=title_font, fill=(10, 10, 10))
    # النص باللون الذهبي
    draw.text((tx, ty), surah_title, font=title_font, fill=(245, 215, 110))

    # --- رسم اسم الشيخ ---
    sheikh_text = fix_arabic_text("الشيخ محمد صديق المنشاوي")
    s_bbox = draw.textbbox((0, 0), sheikh_text, font=sub_font)
    s_tw = s_bbox[2] - s_bbox[0]
    s_tx = (1920 - s_tw) // 2
    
    # ظل أسود
    draw.text((s_tx + 4, 650 + 4), sheikh_text, font=sub_font, fill=(10, 10, 10))
    # النص باللون الأبيض الساطع
    draw.text((s_tx, 650), sheikh_text, font=sub_font, fill=(255, 255, 255))

    thumb_img.save("thumbnail_final.jpg", quality=100)
    print("✅ تم تصميم الغلاف النهائي وحفظه بنجاح.")

    # 7. التصدير النهائي للفيديو عبر FFmpeg
    print("جاري دمج الفيديو (صورة + صوت)...")
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
    print("🚀 تم إنتاج الفيديو والمحتوى بالكامل بنجاح!")

if __name__ == "__main__":
    main()
