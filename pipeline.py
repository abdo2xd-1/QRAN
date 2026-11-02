import os
import re
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    # تنظيف صارم جداً: الاحتفاظ بالحروف العربية والمسافات فقط (يمنع انقلاب النص تماماً)
    clean = re.sub(r'[^\u0621-\u064A\s]', '', text).strip()
    reshaped = arabic_reshaper.reshape(clean)
    return get_display(reshaped)

def download_file(url, target_path):
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

def get_pexels_image(query, api_key, output_path, image_index=0):
    """جلب صورة عالية الجودة من Pexels وتجهيزها بأبعاد 1080p"""
    print(f"جاري جلب صورة من Pexels للبحث: {query}...")
    url = f"https://api.pexels.com/v1/search?query={query}&orientation=landscape&size=large&per_page=5"
    headers = {"Authorization": api_key}
    
    try:
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code == 200:
            data = res.json()
            if data.get("photos") and len(data["photos"]) > image_index:
                # استخدام جودة large2x العالية
                img_url = data["photos"][image_index]["src"]["large2x"]
                download_file(img_url, "temp_pexels.jpg")
                
                # ضبط الأبعاد إلى 1920x1080
                img = Image.open("temp_pexels.jpg").convert("RGB")
                img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
                img.save(output_path, quality=95)
                print(f"✅ تم حفظ الصورة بنجاح: {output_path}")
                return True
        print(f"تنبيه: لم يتم العثور على نتائج كافية في Pexels ({res.status_code})")
    except Exception as e:
        print(f"خطأ في الاتصال بـ Pexels: {e}")
    
    # خلفية احتياطية في حال فشل API بكسلز
    Image.new("RGB", (1920, 1080), (30, 40, 30)).save(output_path)
    return False

def main():
    surah_num = int(os.environ.get("SURAH_NUMBER", "1").strip())
    pexels_key = os.environ.get("API_KEY", "").strip()

    if not pexels_key:
        raise ValueError("لم يتم العثور على مفتاح Pexels في الأسرار (API_KEY)!")

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
    print("جاري تحميل الصوت...")
    download_file(f"https://server10.mp3quran.net/minsh/{surah_num:03d}.mp3", audio_file)

    # 3. تحميل الخط
    font_file = "Amiri-Bold.ttf"
    if not os.path.exists(font_file):
        download_file("https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf", font_file)

    # 4. تجهيز خلفية الفيديو عبر Pexels
    # استخدام صور للمصحف أو مساجد من الداخل
    get_pexels_image("quran book islam", pexels_key, "bg_video.jpg", image_index=0)

    # 5. تجهيز الغلاف عبر Pexels (صورة مختلفة عن الفيديو)
    get_pexels_image("islamic architecture mosque", pexels_key, "thumb_raw.jpg", image_index=1)

    # 6. تصميم الغلاف والكتابة عليه
    thumb_img = Image.open("thumb_raw.jpg").convert("RGBA")
    
    # إضافة طبقة سوداء شفافة لتبريز النص الذهبي وجعله مقروءاً بوضوح
    overlay = Image.new("RGBA", thumb_img.size, (0, 0, 0, 140))
    thumb_img = Image.alpha_composite(thumb_img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(thumb_img)
    title_font = ImageFont.truetype(font_file, 160)
    sub_font = ImageFont.truetype(font_file, 70)

    # حساب المنتصف لكتابة اسم السورة
    bbox = draw.textbbox((0, 0), surah_title, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (1920 - tw) // 2
    ty = 400

    # رسم ظل عميق ثم النص الذهبي
    draw.text((tx + 5, ty + 5), surah_title, font=title_font, fill=(0, 0, 0))
    draw.text((tx, ty), surah_title, font=title_font, fill=(245, 215, 110))

    # كتابة اسم الشيخ تحتها
    sheikh_text = fix_arabic_text("الشيخ محمد صديق المنشاوي")
    s_bbox = draw.textbbox((0, 0), sheikh_text, font=sub_font)
    s_tw = s_bbox[2] - s_bbox[0]
    s_tx = (1920 - s_tw) // 2
    
    draw.text((s_tx + 3, 650 + 3), sheikh_text, font=sub_font, fill=(0, 0, 0))
    draw.text((s_tx, 650), sheikh_text, font=sub_font, fill=(255, 255, 255))

    thumb_img.save("thumbnail_final.jpg", quality=95)
    print("✅ تم تصميم الغلاف بنجاح.")

    # 7. التصدير بـ FFmpeg
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
    print("🚀 تم إنتاج الفيديو من صور Pexels بنجاح!")

if __name__ == "__main__":
    main()
