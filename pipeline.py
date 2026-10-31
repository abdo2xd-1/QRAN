import os
import sys
import json
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# القاموس الشامل لجميع سور القرآن الـ 114
SURAHS = {
    1: {"name": "سورة الفاتحة", "file": "001.mp3"},
    2: {"name": "سورة البقرة", "file": "002.mp3"},
    3: {"name": "سورة آل عمران", "file": "003.mp3"},
    4: {"name": "سورة النساء", "file": "004.mp3"},
    5: {"name": "سورة المائدة", "file": "005.mp3"},
    6: {"name": "سورة الأنعام", "file": "006.mp3"},
    7: {"name": "سورة الأعراف", "file": "007.mp3"},
    8: {"name": "سورة الأنفال", "file": "008.mp3"},
    9: {"name": "سورة التوبة", "file": "009.mp3"},
    10: {"name": "سورة يونس", "file": "010.mp3"},
    11: {"name": "سورة هود", "file": "011.mp3"},
    12: {"name": "سورة يوسف", "file": "012.mp3"},
    13: {"name": "سورة الرعد", "file": "013.mp3"},
    14: {"name": "سورة إبراهيم", "file": "014.mp3"},
    15: {"name": "سورة الحجر", "file": "015.mp3"},
    16: {"name": "سورة النحل", "file": "016.mp3"},
    17: {"name": "سورة الإسراء", "file": "017.mp3"},
    18: {"name": "سورة الكهف", "file": "018.mp3"},
    19: {"name": "سورة مريم", "file": "019.mp3"},
    20: {"name": "سورة طه", "file": "020.mp3"},
    21: {"name": "سورة الأنبياء", "file": "021.mp3"},
    22: {"name": "سورة الحج", "file": "022.mp3"},
    23: {"name": "سورة المؤمنون", "file": "023.mp3"},
    24: {"name": "سورة النور", "file": "024.mp3"},
    25: {"name": "سورة الفرقان", "file": "025.mp3"},
    26: {"name": "سورة الشعراء", "file": "026.mp3"},
    27: {"name": "سورة النمل", "file": "027.mp3"},
    28: {"name": "سورة القصص", "file": "028.mp3"},
    29: {"name": "سورة العنكبوت", "file": "029.mp3"},
    30: {"name": "سورة الروم", "file": "030.mp3"},
    31: {"name": "سورة لقمان", "file": "031.mp3"},
    32: {"name": "سورة السجدة", "file": "032.mp3"},
    33: {"name": "سورة الأحزاب", "file": "033.mp3"},
    34: {"name": "سورة سبأ", "file": "034.mp3"},
    35: {"name": "سورة فاطر", "file": "035.mp3"},
    36: {"name": "سورة يس", "file": "036.mp3"},
    37: {"name": "سورة الصافات", "file": "037.mp3"},
    38: {"name": "سورة ص", "file": "038.mp3"},
    39: {"name": "سورة الزمر", "file": "039.mp3"},
    40: {"name": "سورة غافر", "file": "040.mp3"},
    41: {"name": "سورة فصلت", "file": "041.mp3"},
    42: {"name": "سورة الشورى", "file": "042.mp3"},
    43: {"name": "سورة الزخرف", "file": "043.mp3"},
    44: {"name": "سورة الدخان", "file": "044.mp3"},
    45: {"name": "سورة الجاثية", "file": "045.mp3"},
    46: {"name": "سورة الأحقاف", "file": "046.mp3"},
    47: {"name": "سورة محمد", "file": "047.mp3"},
    48: {"name": "سورة الفتح", "file": "048.mp3"},
    49: {"name": "سورة الحجرات", "file": "049.mp3"},
    50: {"name": "سورة ق", "file": "050.mp3"},
    51: {"name": "سورة الذاريات", "file": "051.mp3"},
    52: {"name": "سورة الطور", "file": "052.mp3"},
    53: {"name": "سورة النجم", "file": "053.mp3"},
    54: {"name": "سورة القمر", "file": "054.mp3"},
    55: {"name": "سورة الرحمن", "file": "055.mp3"},
    56: {"name": "سورة الواقعة", "file": "056.mp3"},
    57: {"name": "سورة الحديد", "file": "057.mp3"},
    58: {"name": "سورة المجادلة", "file": "058.mp3"},
    59: {"name": "سورة الحشر", "file": "059.mp3"},
    60: {"name": "سورة الممتحنة", "file": "060.mp3"},
    61: {"name": "سورة الصف", "file": "061.mp3"},
    62: {"name": "سورة الجمعة", "file": "062.mp3"},
    63: {"name": "سورة المنافقون", "file": "063.mp3"},
    64: {"name": "سورة التغابن", "file": "064.mp3"},
    65: {"name": "سورة الطلاق", "file": "065.mp3"},
    66: {"name": "سورة التحريم", "file": "066.mp3"},
    67: {"name": "سورة الملك", "file": "067.mp3"},
    68: {"name": "سورة القلم", "file": "068.mp3"},
    69: {"name": "سورة الحاقة", "file": "069.mp3"},
    70: {"name": "سورة المعارج", "file": "070.mp3"},
    71: {"name": "سورة نوح", "file": "071.mp3"},
    72: {"name": "سورة الجن", "file": "072.mp3"},
    73: {"name": "سورة المزمل", "file": "073.mp3"},
    74: {"name": "سورة المدثر", "file": "074.mp3"},
    75: {"name": "سورة القيامة", "file": "075.mp3"},
    76: {"name": "سورة الإنسان", "file": "076.mp3"},
    77: {"name": "سورة المرسلات", "file": "077.mp3"},
    78: {"name": "سورة النبأ", "file": "078.mp3"},
    79: {"name": "سورة النازعات", "file": "079.mp3"},
    80: {"name": "سورة عبس", "file": "080.mp3"},
    81: {"name": "سورة التكوير", "file": "081.mp3"},
    82: {"name": "سورة الانفطار", "file": "082.mp3"},
    83: {"name": "سورة المطففين", "file": "083.mp3"},
    84: {"name": "سورة الانشقاق", "file": "084.mp3"},
    85: {"name": "سورة البروج", "file": "085.mp3"},
    86: {"name": "سورة الطارق", "file": "086.mp3"},
    87: {"name": "سورة الأعلى", "file": "087.mp3"},
    88: {"name": "سورة الغاشية", "file": "088.mp3"},
    89: {"name": "سورة الفجر", "file": "089.mp3"},
    90: {"name": "سورة البلد", "file": "090.mp3"},
    91: {"name": "سورة الشمس", "file": "091.mp3"},
    92: {"name": "سورة الليل", "file": "092.mp3"},
    93: {"name": "سورة الضحى", "file": "093.mp3"},
    94: {"name": "سورة الشرح", "file": "094.mp3"},
    95: {"name": "سورة التين", "file": "095.mp3"},
    96: {"name": "سورة العلق", "file": "096.mp3"},
    97: {"name": "سورة القدر", "file": "097.mp3"},
    98: {"name": "سورة البينة", "file": "098.mp3"},
    99: {"name": "سورة الزلزلة", "file": "099.mp3"},
    100: {"name": "سورة العاديات", "file": "100.mp3"},
    101: {"name": "سورة القارعة", "file": "101.mp3"},
    102: {"name": "سورة التكاثر", "file": "102.mp3"},
    103: {"name": "سورة العصر", "file": "103.mp3"},
    104: {"name": "سورة الهمزة", "file": "104.mp3"},
    105: {"name": "سورة الفيل", "file": "105.mp3"},
    106: {"name": "سورة قريش", "file": "106.mp3"},
    107: {"name": "سورة الماعون", "file": "107.mp3"},
    108: {"name": "سورة الكوثر", "file": "108.mp3"},
    109: {"name": "سورة الكافرون", "file": "109.mp3"},
    110: {"name": "سورة النصر", "file": "110.mp3"},
    111: {"name": "سورة المسد", "file": "111.mp3"},
    112: {"name": "سورة الإخلاص", "file": "112.mp3"},
    113: {"name": "سورة الفلق", "file": "113.mp3"},
    114: {"name": "سورة الناس", "file": "114.mp3"},
}

def get_access_token(client_id, client_secret, refresh_token):
    print("جاري تجديد Access Token الخاص بـ YouTube API...")
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post("https://oauth2.googleapis.com/token", data=payload, headers=headers).json()
    if "access_token" not in res:
        print("خطأ في تجديد التوكن:", res)
        sys.exit(1)
    return res["access_token"]

def download_audio(surah_num):
    filename = SURAHS[surah_num]["file"]
    url = f"https://server10.mp3quran.net/minsh/{filename}"
    print(f"جاري تنزيل الملف الصوتي: {url}")
    r = requests.get(url, stream=True)
    with open("audio.mp3", "wb") as f:
        for chunk in r.iter_content(chunk_size=16384):
            f.write(chunk)
    print("اكتمل تنزيل التلاوة الصوتية بنجاح.")

def create_thumbnail(surah_name):
    print(f"جاري تصميم الصورة المصغرة لـ: {surah_name}...")
    img = Image.open("assets/thumb_template.jpg").convert("RGB")
    draw = ImageDraw.Draw(img)
    
    reshaped_text = arabic_reshaper.reshape(surah_name)
    bidi_text = get_display(reshaped_text)
    
    font = ImageFont.truetype("assets/font.ttf", 95)
    
    bbox = draw.textbbox((0, 0), bidi_text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    x = 730 - (w / 2)
    y = 230 - (h / 2)
    
    draw.text((x + 4, y + 4), bidi_text, font=font, fill=(20, 15, 10))
    draw.text((x, y), bidi_text, font=font, fill=(245, 215, 135))
    
    img.save("thumbnail_final.jpg", quality=95)
    print("تم تجهيز الصورة المصغرة النهائية.")

def build_video():
    print("جاري دمج الفيديو وإضافة طبقة الحبيبات السينمائية (Film Grain Noise) عبر FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", "assets/background.jpg",
        "-i", "audio.mp3",
        "-filter_complex",
        "[0:v]scale=1920:1080,noise=alls=14:allf=t+p[v_noisy];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a_norm]",
        "-map", "[v_noisy]",
        "-map", "[a_norm]",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "output.mp4"
    ]
    subprocess.run(cmd, check=True)
    print("تم إنشاء ملف الفيديو output.mp4 بنجاح.")

def upload_to_youtube(access_token, surah_name):
    title = f"{surah_name} كاملة بصوت هادئ يريح القلب | الشيخ محمد صديق المنشاوي (تسجيل نقي)"
    description = f"""تلاوة خاشعة مباركة لـ {surah_name} بصوت فضيلة الشيخ محمد صديق المنشاوي (رحمه الله).
تسجيل إذاعي تاريخي نقي وهادئ بدون صدى صوت لمساعدتك على التدبر والسكينة.

القارئ: فضيلة الشيخ محمد صديق المنشاوي
الرواية: حفص عن عاصم

صدقة جارية لنا ولكم ولوالدينا ولموتانا وموتى المسلمين جميعاً.
#المنشاوي #{surah_name.replace(' ', '_')} #تلاوات_خاشعة #قرآن_كريم"""

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["المنشاوي", surah_name, "قرآن", "تلاوة خاشعة", "بدون صدى صوت", "نوم وهدوء", "سورة"],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    print("بدء جلسة الرفع التتابعي (Resumable Upload Session)...")
    init_res = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers=headers,
        data=json.dumps(metadata)
    )
    
    if init_res.status_code != 200:
        print("خطأ في بدء جلسة الرفع:", init_res.text)
        sys.exit(1)
        
    upload_url = init_res.headers.get("Location")

    print("جاري رفع ملف الفيديو إلى القناة الآن...")
    with open("output.mp4", "rb") as f:
        video_res = requests.put(
            upload_url,
            headers={"Content-Type": "video/mp4"},
            data=f
        ).json()
    
    video_id = video_res.get("id")
    if not video_id:
        print("خطأ في رفع الفيديو:", video_res)
        sys.exit(1)
        
    print(f"تم رفع الفيديو بنجاح! الرابط: https://youtu.be/{video_id}")

    print("جاري رفع الصورة المصغرة المخصصة...")
    with open("thumbnail_final.jpg", "rb") as thumb_f:
        t_res = requests.post(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"image": ("thumbnail.jpg", thumb_f, "image/jpeg")}
        )
    print("تم تعيين الصورة المصغرة بنجاح:", t_res.status_code)

if __name__ == "__main__":
    surah_num = int(os.environ.get("SURAH_NUMBER", "18").strip())
    surah_data = SURAHS.get(surah_num, SURAHS[18])
    
    c_id = os.environ["CLIENT_ID"].strip()
    c_secret = os.environ["CLIENT_SECRET"].strip()
    r_token = os.environ["REFRESH_TOKEN"].strip()
    
    token = get_access_token(c_id, c_secret, r_token)
    download_audio(surah_num)
    create_thumbnail(surah_data["name"])
    build_video()
    upload_to_youtube(token, surah_data["name"])
