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

def generate_image_with_gemini(client, prompt, output_filename):
    """توليد الصورة عبر Imagen 3 باستخدام مفتاح Gemini API"""
    print(f"جاري توليد {output_filename} عبر Gemini Imagen...")
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
            image = Image.open(io.BytesIO(generated_image.image.image_bytes))
            image.save(output_filename, quality=95)
            print(f"✅ تم توليد {output_filename} بنجاح عبر AI.")
            return True
    except Exception as e:
        print(f"تحذير: حدث خطأ أثناء التوليد عبر Gemini: {e}")
        return False

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    client = None
    if api_key:
        client = genai.Client(api_key=api_key)

    # 1. بيانات السورة
    meta_url = f"https://api.alquran.cloud/v1/surah/{surah_num}"
    res = requests.get(meta_url).json()
    raw_name = res["data"]["name"]
    surah_title = fix_arabic_text(raw_name)

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")
    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة مباركة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.")

    # 2. تحميل الصوت
    audio_file = "audio.mp3"
    audio_url = f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3"
    print("تحميل الصوت...")
    download_file(audio_url, audio_file)

    # 3. تحميل الخط العربي
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. توليد خلفية الفيديو التراثية
    video_prompt = (
        "Cinematic cozy traditional islamic heritage room, an open Quran on a wooden stand (rehal) "
        "placed on a vintage red Persian carpet, an antique vintage brown radio next to it, "
        "a traditional glowing lantern candle, an open ornate wooden mashrabiya window overlooking a minaret at sunset, "
        "warm cinematic lighting, photorealistic 8k, historical aesthetic, no people"
    )
    
    bg_success = False
    if client:
        bg_success = generate_image_with_gemini(client, video_prompt, "bg_video.jpg")
    
    if not bg_success and not os.path.exists("bg_video.jpg"):
        img = Image.new("RGB", (1920, 1080), (28, 20, 14))
        img.save("bg_video.jpg")

    # 5. توليد الغلاف (المنشاوي والإطار الإسلامي)
    thumb_prompt = (
        "Islamic youtube thumbnail background, luxury dark green and gold arabesque Islamic geometric patterns, "
        "ornate golden calligraphy frame banner in center right, empty space for text inside the frame, "
        "left side showing portrait of Sheikh Muhammad Siddiq Al-Minshawi with white amama and traditional azhar gown, "
        "golden ornate Quran on wooden rehal at bottom, professional graphic design, 8k resolution"
    )

    thumb_success = False
    if client:
        thumb_success = generate_image_with_gemini(client, thumb_prompt, "thumb_raw.jpg")

    if thumb_success and os.path.exists("thumb_raw.jpg"):
        thumb_img = Image.open("thumb_raw.jpg").convert("RGB").resize((1920, 1080))
    else:
        thumb_img = Image.open("bg_video.jpg").convert("RGB").resize((1920, 1080))

    # كتابة اسم السورة داخل الإطار
    draw = ImageDraw.Draw(thumb_img)
    font = ImageFont.truetype(font_file, 130)
    bbox = draw.textbbox((0, 0), surah_title, font=font)
    tw = bbox[2] - bbox[0]
    tx = int(1920 * 0.58) - (tw // 2)
    ty = int(1080 * 0.40)

    draw.text((tx + 4, ty + 4), surah_title, font=font, fill=(0, 0, 0))
    draw.text((tx, ty), surah_title, font=font, fill=(245, 215, 110))

    thumb_img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم حفظ الصورة المصغرة النهائية.")

    # 6. الدمج بـ FFmpeg
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
    print("🚀 تم إنتاج الفيديو والصورة بنجاح عبر الذكاء الاصطناعي!")

if __name__ == "__main__":
    main()
