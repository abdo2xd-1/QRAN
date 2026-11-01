import os
import re
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def clean_and_fix_arabic(text):
    """إزالة علامات التشكيل المعقدة لضبط اتصال الكلمات العربية واتجاهها تماماً"""
    # إزالة التشكيل وحركات المصحف
    tashkeel_regex = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]')
    text_clean = re.sub(tashkeel_regex, '', text)
    
    # تصحيح الاتصال وتعديل الاتجاه من اليمين لليسار
    configuration = {
        'delete_harakat': True,
        'support_ligatures': True
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration)
    reshaped_text = reshaper.reshape(text_clean)
    return get_display(reshaped_text)

def download_file(url, target_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def main():
    surah_num = os.environ.get("SURAH_NUMBER", "1").strip()
    surah_num_int = int(surah_num)

    # 1. جلب اسم السورة
    meta_url = f"https://api.alquran.cloud/v1/surah/{surah_num_int}"
    meta_res = requests.get(meta_url).json()
    raw_name = meta_res["data"]["name"]
    surah_name_clean = clean_and_fix_arabic(raw_name)

    print(f"تم اختيار: {raw_name} -> بعد التصحيح: {surah_name_clean}")

    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{raw_name} كاملة بصوت الشيخ محمد صديق المنشاوي")

    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة خاشعة لـ {raw_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.\n\nاستمع للقرآن الكريم بجودة عالية.")

    # 2. تحميل تلاوة الشيخ المنشاوي
    audio_num_str = f"{surah_num_int:03d}"
    audio_url = f"https://server10.mp3quran.net/minsh/{audio_num_str}.mp3"
    audio_file = "audio.mp3"
    print(f"جاري تحميل الصوت: {audio_url}")
    download_file(audio_url, audio_file)

    # 3. تحميل الخط العربي الأصيل
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf"
        download_file(font_url, font_file)

    # 4. تجهيز الصورة المصغرة (Thumbnail)
    thumb_w, thumb_h = 1920, 1080
    
    # البحث عن القالب بأي امتداد كان
    template_path = None
    for ext in ["png", "jpg", "jpeg", "PNG", "JPG"]:
        if os.path.exists(f"thumb_template.{ext}"):
            template_path = f"thumb_template.{ext}"
            break

    if template_path:
        print(f"تم العثور على قالب الغلاف: {template_path}")
        thumb_img = Image.open(template_path).convert("RGBA").resize((thumb_w, thumb_h))
    else:
        print("تحذير: لم يتم العثور على thumb_template، جاري إنشاء خلفية افتراضية.")
        thumb_img = Image.new("RGBA", (thumb_w, thumb_h), color=(18, 25, 20, 255))

    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 130)

    # حساب موقع الكتابة في منتصف الإطار المخصص
    bbox = draw.textbbox((0, 0), surah_name_clean, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = int(thumb_w * 0.58) - (tw // 2)
    ty = int(thumb_h * 0.38)

    # رسم ظل ثم كتابة النص باللون الذهبي
    draw.text((tx + 4, ty + 4), surah_name_clean, font=title_font, fill=(0, 0, 0, 240))
    draw.text((tx, ty), surah_name_clean, font=title_font, fill=(245, 215, 110))

    thumb_final = thumb_img.convert("RGB")
    thumb_final.save("thumbnail_final.jpg", quality=95)

    # 5. اختيار خلفية الفيديو التراثية
    video_bg = None
    for ext in ["jpg", "jpeg", "png", "JPG", "PNG"]:
        if os.path.exists(f"bg_video.{ext}"):
            video_bg = f"bg_video.{ext}"
            break

    if not video_bg:
        print("تحذير: لم يتم العثور على bg_video، سيتم استخدام صورة الغلاف.")
        video_bg = "thumbnail_final.jpg"
    else:
        print(f"تم العثور على خلفية الفيديو: {video_bg}")

    # 6. دمج الصوت مع الصورة عبر FFmpeg
    print("جاري تصدير الفيديو عبر FFmpeg...")
    ffmpeg_cmd = [
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
    subprocess.run(ffmpeg_cmd, check=True)
    print("✅ تم بنجاح إنتاج الفيديو والصورة المصغرة السليمة!")

if __name__ == "__main__":
    main()
