import os
import re
import urllib.parse
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    """تهيئة النص العربي للطباعة السليمة (بدون عكس يدوي لتجنب تعارض الخوادم)"""
    # إزالة تشكيل القرآن والرموز المزعجة
    clean = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text).strip()
    
    # إعادة تشكيل الحروف العربية وربطها (دون عكس الاتجاه)
    reshaper = arabic_reshaper.ArabicReshaper({
        'delete_harakat': True,
        'support_ligatures': True,
        'shift_harakat_position': False
    })
    reshaped_text = reshaper.reshape(clean)
    
    # استخدام خوارزمية bidi القياسية لضبط الاتجاه النهائي
    return get_display(reshaped_text)

def download_file(url, target_path):
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

def get_huggingface_image(prompt, hf_token, output_path):
    """
    استخدام نموذج Hugging Face FLUX.1 (أفضل وأسرع نموذج مجاني للصور)
    يعمل بشكل ممتاز لإنتاج صور خالية تماماً من العلامات المائية.
    """
    print(f"جاري طلب توليد الصورة عبر Hugging Face: {output_path}...")
    
    # استخدام نموذج سريع جداً (FLUX.1-schnell)
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }
    # نطلب صورة بأبعاد 16:9 العريضة (1024x576 هو أقصى حد للنسخة المجانية، سنكبره لاحقاً)
    payload = {
        "inputs": prompt,
        "parameters": {"width": 1024, "height": 576}
    }

    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=90)
        if res.status_code == 200:
            # تحميل الصورة وتكبيرها فورا إلى 1080p بجودة ممتازة
            img = Image.open(io.BytesIO(res.content)).convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
            img.save(output_path, quality=95)
            print(f"✅ تم توليد وتجهيز الصورة بنجاح: {output_path}")
            return True
        else:
            print(f"استجابة غير متوقعة من API: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"خطأ في الاتصال بالذكاء الاصطناعي: {e}")

    # في حال فشل الـ API (نادر الحدوث مع التوكن الصحيح)، ننشئ خلفية لونية احتياطية
    print(f"⚠️ فشل توليد الصورة. سيتم استخدام خلفية احتياطية لـ {output_path}.")
    Image.new("RGB", (1920, 1080), (28, 20, 14)).save(output_path)
    return False

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())
    hf_token = os.environ.get("API_KEY", "").strip()

    if not hf_token:
        print("❌ خطأ: لم يتم العثور على توكن Hugging Face (API_KEY) في الأسرار!")
        return

    # 1. بيانات السورة
    meta = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
    raw_name = meta["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل الصوت
    audio_file = "audio.mp3"
    print("جاري تحميل التلاوة...")
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
    get_huggingface_image(bg_prompt, hf_token, "bg_video.jpg")

    # 5. توليد خلفية الغلاف
    thumb_prompt = (
        "Luxury Islamic background, dark green and gold arabesque patterns, "
        "ornate golden calligraphy frame banner in center right with empty space, "
        "vintage portrait of Egyptian Quran reciter Sheikh Al-Minshawi on the left wearing white turban, 8k, masterpiece"
    )
    get_huggingface_image(thumb_prompt, hf_token, "thumb_raw.jpg")

    # 6. كتابة النص العربي السليم فوق الغلاف المولد
    thumb_img = Image.open("thumb_raw.jpg").convert("RGBA")
    
    # تظليل خفيف لبروز النص
    overlay = Image.new("RGBA", thumb_img.size, (0, 0, 0, 110))
    thumb_img = Image.alpha_composite(thumb_img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 160)
    sub_font = ImageFont.truetype(font_file, 70)

    # كتابة اسم السورة
    bbox = draw.textbbox((0, 0), surah_title, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (1920 - tw) // 2
    ty = 400

    draw.text((tx + 5, ty + 5), surah_title, font=title_font, fill=(0, 0, 0))
    draw.text((tx, ty), surah_title, font=title_font, fill=(245, 215, 110))

    # كتابة اسم القارئ
    sheikh_text = fix_arabic_text("الشيخ محمد صديق المنشاوي")
    s_bbox = draw.textbbox((0, 0), sheikh_text, font=sub_font)
    s_tw = s_bbox[2] - s_bbox[0]
    s_tx = (1920 - s_tw) // 2
    
    draw.text((s_tx + 3, 650 + 3), sheikh_text, font=sub_font, fill=(0, 0, 0))
    draw.text((s_tx, 650), sheikh_text, font=sub_font, fill=(255, 255, 255))

    thumb_img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم تصميم الغلاف بنجاح بالنص العربي السليم.")

    # 7. التصدير بـ FFmpeg
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
    print("🚀 تم إنتاج الفيديو والغلاف بالذكاء الاصطناعي بنجاح تام!")

if __name__ == "__main__":
    main()
