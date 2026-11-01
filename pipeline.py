import os
import re
import io
import time
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # إزالة حركات التشكيل وحركات المصحف لضمان اتصال الحروف وعدم قلبها
    clean_text = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
    reshaped = arabic_reshaper.reshape(clean_text)
    return get_display(reshaped)

def download_file(url, target_path):
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def query_huggingface_image(prompt, hf_token, output_path):
    """توليد صورة واقعية 1080p عبر Hugging Face Inference API"""
    print(f"جاري توليد الصورة عبر Hugging Face AI: {output_path}...")
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}

    for attempt in range(4):
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=120)
            if res.status_code == 200:
                image = Image.open(io.BytesIO(res.content)).convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
                image.save(output_path, quality=95)
                print(f"✅ تم توليد وحفظ: {output_path}")
                return True
            elif res.status_code == 503:
                data = res.json()
                wait_time = int(data.get("estimated_time", 25))
                print(f"النموذج قيد التحميل في سيرفرات Hugging Face، انتظر {wait_time} ثانية...")
                time.sleep(wait_time)
            else:
                print(f"تنبيه الـ API: استجابة {res.status_code} - {res.text}")
                time.sleep(5)
        except Exception as e:
            print(f"خطأ أثناء الاتصال: {e}")
            time.sleep(5)
            
    print(f"فشل توليد {output_path}، سيتم استخدام خلفية تراثية احتياطية.")
    return False

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())
    hf_token = os.environ.get("API_KEY", "").strip()

    if not hf_token:
        print("تحذير: لم يتم العثور على API_KEY في Secrets!")

    # 1. جلب بيانات السورة
    meta_url = f"https://api.alquran.cloud/v1/surah/{surah_num}"
    res = requests.get(meta_url).json()
    raw_name = res["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    print(f"السورة الحالية: {raw_name}")

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل تلاوة المنشاوي (MP3)
    audio_file = "audio.mp3"
    audio_url = f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3"
    print("جاري تحميل الصوت...")
    download_file(audio_url, audio_file)

    # 3. تحميل الخط العربي الأصيل
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. توليد خلفية الفيديو التراثية (غرفة قديمة، مصحف، راديو خشبي، نافذة ومئذنة)
    bg_prompt = (
        "Cinematic ultra detailed cozy traditional Islamic heritage room, open Holy Quran on wooden rehal stand, "
        "vintage brown wooden radio, warm candle lantern on authentic Persian carpet, "
        "open mashrabiya window overlooking a mosque minaret during golden hour sunset, warm tones, photorealistic 8k, no text, no people"
    )
    if not query_huggingface_image(bg_prompt, hf_token, "bg_video.jpg"):
        img = Image.new("RGB", (1920, 1080), (28, 20, 14))
        img.save("bg_video.jpg")

    # 5. توليد الغلاف الإسلامي (صورة الشيخ والزخارف الذهبية)
    thumb_prompt = (
        "Islamic luxury youtube thumbnail background, dark green and gold arabesque Islamic geometric patterns, "
        "large empty ornate golden calligraphy frame in center right, "
        "portrait of Egyptian Quran reciter Sheikh Al-Minshawi on the left wearing white turban, "
        "golden ornate details, 8k resolution, professional graphic design, empty banner space for typography"
    )
    if not query_huggingface_image(thumb_prompt, hf_token, "thumb_raw.jpg"):
        thumb_img = Image.open("bg_video.jpg").convert("RGB")
    else:
        thumb_img = Image.open("thumb_raw.jpg").convert("RGB")

    # كتابة اسم السورة بالخط المتصل واللون الذهبي فوق الغلاف
    draw = ImageDraw.Draw(thumb_img)
    font = ImageFont.truetype(font_file, 130)

    bbox = draw.textbbox((0, 0), surah_title, font=font)
    tw = bbox[2] - bbox[0]
    tx = int(1920 * 0.58) - (tw // 2)
    ty = int(1080 * 0.40)

    # ظل أسود عميق ثم النص الذهبي
    draw.text((tx + 4, ty + 4), surah_title, font=font, fill=(10, 10, 10))
    draw.text((tx, ty), surah_title, font=font, fill=(245, 215, 110))

    thumb_img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم حفظ الغلاف النهائي بنجاح.")

    # 6. دمج الصوت مع خلفية الفيديو التراثية عبر FFmpeg
    print("جاري تصدير الفيديو النهائي...")
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
    print("🚀 تم اكتمال العملية بنجاح! تم إنتاج الفيديو والغلاف بالذكاء الاصطناعي بالكامل.")

if __name__ == "__main__":
    main()
