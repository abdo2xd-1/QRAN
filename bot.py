import os
import subprocess
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# استهداف القناة
target_channel = "https://www.youtube.com/@tilawat.quraniat.khalida/videos"
print("=== جاري البحث عن أحدث فيديو في القناة المستهدفة ===")

ydl_opts = {
    'extract_flat': False,
    'max_downloads': 1,
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'outtmpl': 'downloaded_video.%(ext)s',
    # مفيش حاجة للكوكيز هنا لأن جهازك مش محظور!
}

video_title = "تلاوة قرآنية مباركة"
video_desc = "تلاوة خاشعة تريح القلوب"

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(target_channel, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            latest_video = info['entries'][0]
            video_url = latest_video.get('webpage_url')
            video_title = latest_video.get('title', video_title)
            video_desc = latest_video.get('description', video_desc)
            print(f"تم العثور على الفيديو: {video_title}")
            ydl.download([video_url])
        else:
            print("لم يتم العثور على فيديوهات.")
            exit(1)
except Exception as e:
    print(f"حدث خطأ أثناء التحميل: {e}")
    exit(1)

input_file = "downloaded_video.mp4"
output_file = "watermarked_video.mp4"

print("=== جاري وضع العلامة المائية باستخدام FFmpeg ===")
watermark_text = "قناتك المباركة"

ffmpeg_cmd = [
    "ffmpeg", "-i", input_file,
    "-vf", f"drawtext=text='{watermark_text}':x=w-tw-20:y=h-th-20:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5",
    "-codec:a", "copy", "-y", output_file
]
subprocess.run(ffmpeg_cmd)

print("=== جاري الرفع على يوتيوب ===")
# ضع مفاتيحك هنا مباشرة (احذر من مشاركة هذا الملف مع أحد)
client_id = "ضع_الـ_CLIENT_ID_هنا"
client_secret = "ضع_الـ_CLIENT_SECRET_هنا"
refresh_token = "ضع_الـ_REFRESH_TOKEN_هنا"

creds = Credentials(
    None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret
)

youtube = build("youtube", "v3", credentials=creds)
media = MediaFileUpload(output_file, chunksize=1024*1024, resumable=True)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "categoryId": "22",
            "title": video_title,
            "description": video_desc + "\n\n#القرآن_الكريم #تلاوة_خاشعة",
            "tags": ["القرآن_الكريم", "تلاوة_خاشعة", "قرآن"]
        },
        "status": {
            "privacyStatus": "public"
        }
    },
    media_body=media
)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"تم رفع {int(status.progress() * 100)}% ...")

print(f"تم بنجاح! الرابط: https://youtu.be/{response['id']}")

# تنظيف الملفات بعد الرفع لتوفير المساحة
if os.path.exists(input_file): os.remove(input_file)
if os.path.exists(output_file): os.remove(output_file)
