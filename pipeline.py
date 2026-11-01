import os
import sys
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic(text):
    """ربط الحروف وضبط اتجاه القراءة من اليمين لليسار"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def download_file(url, target_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def main():
    surah_num = os.environ.get("SURAH_NUMBER", "1").strip()
    surah_num_int = int(surah_num)

    # 1. جلب اسم وبيانات السورة
    meta_url = f"https://api.alquran.cloud/v1/surah/{surah_num_int}"
    meta_res = requests.get(meta_url).json()
    surah_name = meta_res["data"]["name"]
    print(f"تم اختيار السورة: {surah_name}")

    # حفظ نصوص العنوان والوصف
    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(f"{surah_name} كاملة بصوت الشيخ محمد صديق المنشاوي")

    with open("desc.txt", "w", encoding="utf-8") as f:
        f.write(f"تلاوة خاشعة لـ {surah_name} بصوت القارئ الشيخ محمد صديق المنشاوي رحمة الله عليه.\n\nاستمع للقرآن الكريم بجودة عالية.")

    # 2. تحميل ملف الصوت للشيخ المنشاوي (مرتل)
    audio_num_str = f"{surah_num_int:03d}"
    audio_url = f"https://server10.mp3quran.net/minsh/{audio_num_str}.mp3"
    audio_file = "audio.mp3"
    print(f"جاري تحميل الصوت من: {audio_url}")
    download_file(audio_url, audio_file)

    # 3. تحميل الخط العربي
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf"
        print("جاري تحميل الخط العربي...")
        download_file(font_url, font_file)

    # 4. تجهيز وتوليد الصورة المصغرة (Thumbnail)
    thumb_w, thumb_h = 1920, 1080
    if os.path.exists("thumb_template.png"):
        thumb_img = Image.open("thumb_template.png").convert("RGBA").resize((thumb_w, thumb_h))
    elif os.path.exists("thumb_template.jpg"):
        thumb_img = Image.open("thumb_template.jpg").convert("RGBA").resize((thumb_w, thumb_h))
    else:
        # خلفية إسلامية كحلية/زيتونية افتراضية في حال عدم رفع القالب
        thumb_img = Image.new("RGBA", (thumb_w, thumb_h), color=(18, 25, 20, 255))

    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 130)

    # كتابة اسم السورة في الإطار
    s_text = fix_arabic(surah_name)
    bbox = draw.textbbox((0, 0), s_text, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = int(thumb_w * 0.58) - (tw // 2)
    ty = int(thumb_h * 0.38)

    # إضافة ظل للنص ثم كتابة النص باللون الذهبي
    draw.text((tx + 4, ty + 4), s_text, font=title_font, fill=(10, 10, 10, 230))
    draw.text((tx, ty), s_text, font=title_font, fill=(245, 215, 110))

    thumb_final = thumb_img.convert("RGB")
    thumb_final.save("thumbnail_final.jpg", quality=95)
    print("✅ تم تجهيز thumbnail_final.jpg بنجاح.")

    # 5. تجهيز خلفية الفيديو المرئية
    video_bg = "bg_video.jpg" if os.path.exists("bg_video.jpg") else "thumbnail_final.jpg"

    # 6. دمج الصوت والصورة عبر FFmpeg
    print("جاري إنتاج الفيديو بواسطة FFmpeg...")
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
    print("✅ تم إنتاج output.mp4 بنجاح!")

if __name__ == "__main__":
    main()
