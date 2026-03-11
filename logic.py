import json
import os
import datetime
import subprocess
import sys
from hijri_converter import Gregorian

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")
URDU_FONT = os.path.join(ASSETS_DIR, "urdu_font.ttf")
ENG_FONT = os.path.join(ASSETS_DIR, "main_font.ttf")

def get_islamic_date():
    try:
        today = datetime.date.today()
        hijri = Gregorian(today.year, today.month, today.day).to_hijri()
        return f"{hijri.day} {hijri.month_name()} {hijri.year} AH"
    except:
        return ""

def download_video(url, filename):
    """Downloads video using yt-dlp for better stability."""
    output_path = os.path.join(DOWNLOAD_DIR, filename)
    # Agar file pehle se maujood hai to dobara download nahi kare ga
    if not os.path.exists(output_path):
        try:
            subprocess.run([
                'yt-dlp', 
                '-o', output_path, 
                '--no-check-certificate',
                url
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            return None
    return output_path

def generate_ffmpeg_command():
    # Load JSON data
    try:
        with open('playlist.json', 'r') as f: play_data = json.load(f)
        with open('bar.json', 'r') as f: bar_data = json.load(f)
        with open('program.json', 'r') as f: prog_data = json.load(f)
        with open('ad.json', 'r') as f: ad_data = json.load(f)
    except Exception as e:
        return f"echo 'JSON Error: {e}'"

    # Download Main Video
    main_video_url = play_data['videos'][0]
    local_video = download_video(main_video_url, "main_video.mp4")
    
    if not local_video:
        return "echo 'Error: Could not download main video.'"

    # Check for Ads
    if ad_data.get('status') == "on":
        ad_local = download_video(ad_data['ad_url'], "ad_video.mp4")
        if ad_local:
            local_video = ad_local

    islamic_date = get_islamic_date()
    
    # FFmpeg Filter Complex (Animations)
    filter_chain = (
        f"[0:v]scale=1280:720,setdar=16/9[bg]; "
        f"[bg]drawbox=y=ih-50:color=blue@0.7:width=iw:height=50:t=fill[v_bar]; "
        f"[v_bar]drawtext=fontfile='{URDU_FONT}':text='{bar_data['text']}':"
        f"x=w-mod(t*100\,w+tw):y=h-40:fontcolor=white:fontsize=28[v_scroll]; "
        f"[1:v]scale=100:-1[logo_s]; "
        f"[v_scroll][logo_s]overlay=main_w-120:main_h-130[v_logo]; "
        f"[v_logo]drawtext=fontfile='{ENG_FONT}':text='{islamic_date}':"
        f"x=main_w-220:y=main_h-40:fontcolor=yellow:fontsize=20[v_date]; "
        f"[v_date]drawtext=fontfile='{ENG_FONT}':text='NOW\: {prog_data['now']}':"
        f"x=20:y=20+10*sin(t*2):fontcolor=white:fontsize=24:box=1:boxcolor=black@0.6[v_prog]"
    )

    command = (
        f"ffmpeg -re -i {local_video} -i {LOGO_PATH} "
        f"-filter_complex \"{filter_chain}\" "
        f"-map \"[v_prog]\" -map 0:a "
        f"-vcodec libx264 -preset veryfast -b:v 2000k -maxrate 2000k -bufsize 4000k "
        f"-acodec aac -b:a 128k "
        f"-f hls -hls_time 6 -hls_list_size 5 -hls_flags delete_segments live/index.m3u8"
    )
    
    return command

if __name__ == "__main__":
    print(generate_ffmpeg_command())
