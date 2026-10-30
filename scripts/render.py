import os
import subprocess
import requests

# 1. رابط التلاوة الصوتية (مثال: سورة البقرة أو مريم للشيخ المنشاوي من الأرشيف أو موقع قرآن)
AUDIO_URL = os.getenv("AUDIO_URL", "https://server10.mp3quran.net/minsh/002.mp3")
AUDIO_FILE = "input_audio.mp3"
PROCESSED_AUDIO = "processed_audio.mp3"
OUTPUT_VIDEO = "final_output.mp4"

def download_audio(url, output_path):
    print(f"Downloading audio from {url}...")
    response = requests.get(url, stream=True)
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    print("Download complete.")

def process_and_render():
    # تنزيل ملف الصوت
    download_audio(AUDIO_URL, AUDIO_FILE)

    # معالجة الصوت: تقليل ضوضاء خفيف + موازنة الصوت (Normalization)
    print("Enhancing audio levels...")
    audio_cmd = [
        "ffmpeg", "-y", "-i", AUDIO_FILE,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,afftdn=nf=-25",
        "-c:a", "libmp3lame", "-b:a", "192k",
        PROCESSED_AUDIO
    ]
    subprocess.run(audio_cmd, check=True)

    # دمج الفيديو فائق السرعة
    # يتم تكرار الخلفية مع وضع صورة القارئ عليها واستخدام الصوت المعالج
    print("Rendering video via FFmpeg stream...")
    video_cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "2", "-i", "assets/background.jpg",
        "-i", "assets/reciter.png",
        "-i", PROCESSED_AUDIO,
        "-filter_complex", "[0:v][1:v]overlay=W-w-100:(H-h)/2[v]",
        "-map", "[v]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-shortest",
        OUTPUT_VIDEO
    ]
    subprocess.run(video_cmd, check=True)
    print(f"Render completed successfully: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    process_and_render()
