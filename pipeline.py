import os
import re
import io
import time
import urllib.parse
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # إزالة تشكيل القرآن والرموز الخاصة
    clean = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text).strip()
    configuration = {
        'delete_harakat': True,
        'support_ligatures': True,
        'shift_harakat_position': False
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration)
    reshaped_text = reshaper.reshape(clean)
    return get_display(reshaped_text)

def download_file(url, target_path):
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_ai_image(prompt, hf_token, output_path):
    print(f"\nجاري طلب توليد الصورة عبر الذكاء الاصطناعي: {output_path}...")
    
    # 1. المحاولة الأولى: Hugging Face (FLUX.1)
    if hf_token:
        print("الاعتماد الأساسي على Hugging Face...")
        api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        payload = {"inputs": prompt, "parameters": {"width": 1024, "height": 576}}
        
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                img = Image.open(io.BytesIO(res.content)).convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
                img.save(output_path, quality=95)
                print(f"✅ تم توليد الصورة بنجاح عبر Hugging Face.")
                return
            else:
                print(f"تنبيه: Hugging Face أرجع الاستجابة {res.status_code}")
        except Exception as e:
            print(f"فشل الاتصال بشبكة Hugging Face: {e}")

    # 2. التبديل التلقائي: Pollinations AI (بديل مجاني لا يحتاج توكن)
    print("جاري التبديل التلقائي لمحرك الذكاء الاصطناعي البديل (Pollinations AI)...")
    try:
        safe_prompt = urllib.parse.quote(prompt)
        # استخدام دقة 720p لتجنب قيود الدفع (402) ثم رفعها لـ 1080p
        poll_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
        res = requests.get(poll_url, timeout=60)
        if res.status_code == 200:
            img = Image.open(io.BytesIO(res.content)).convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
            img.save(output_path, quality=95)
            print(f"✅ تم توليد الصورة بنجاح عبر Pollinations AI.")
            return
    except Exception as e:
        print(f"فشل المحرك البديل أيضاً: {e}")

    # 3. الحماية القصوى: منع فشل الأكشن بالكامل
    print("⚠️ تم إنشاء خلفية لونية احتياطية لضمان عدم تعطل دمج الفيديو...")
    Image.new("RGB", (1920, 1080), (28, 20, 14)).save(output_path)

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())
    hf_token = os.environ.get("API_KEY", "").strip()

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
    download_file(f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3", audio_file)

    # 3. تحميل الخط
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. توليد خلفية الفيديو التراثية
    bg_prompt = (
        "Cinematic ultra detailed shot of cozy traditional Islamic room, open Holy Quran on wooden rehal stand, "
        "vintage wooden radio, warm lantern on Persian carpet, open wooden mashrabiya window overlooking minaret at sunset, 8k, photorealistic"
    )
    generate_ai_image(bg_prompt, hf_token, "bg_video.jpg")

    # 5. توليد الغلاف عبر الـ AI
    thumb_prompt = (
        "Luxury Islamic background, dark green and gold arabesque patterns, "
        "ornate golden calligraphy frame banner in center right with empty space, "
        "vintage portrait of Egyptian Quran reciter Sheikh Al-Minshawi on the left wearing white turban, 8k, masterpiece"
    )
    generate_ai_image(thumb_prompt, hf_token, "thumb_raw.jpg")

    # 6. كتابة النص العربي المضبوط فوق الغلاف
    thumb_img = Image.open("thumb_raw.jpg").convert("RGB")
    draw = ImageDraw.Draw(thumb_img)
    font = ImageFont.truetype(font_file, 130)

    bbox = draw.textbbox((0, 0), surah_title, font=font)
    tw = bbox[2] - bbox[0]
    tx = int(1920 * 0.58) - (tw // 2)
    ty = int(1080 * 0.40)

    draw.text((tx + 4, ty + 4), surah_title, font=font, fill=(0, 0, 0))
    draw.text((tx, ty), surah_title, font=font, fill=(245, 215, 110))
    thumb_img.save("thumbnail_final.jpg", quality=95)

    # 7. التصدير بـ FFmpeg
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
    print("🚀 تم اكتمال توليد الفيديو والغلاف بنجاح!")

if __name__ == "__main__":
    main()
