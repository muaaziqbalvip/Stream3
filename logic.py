import json
import os
import datetime
from hijri_converter import Gregorian

def get_islamic_date():
    today = datetime.date.today()
    hijri = Gregorian(today.year, today.month, today.day).to_hijri()
    return f"{hijri.day} {hijri.month_name()} {hijri.year} AH"

def generate_ffmpeg_command():
    # Load JSONs
    with open('bar.json', 'r') as f: bar_data = json.load(f)
    with open('program.json', 'r') as f: prog_data = json.load(f)
    with open('ad.json', 'r') as f: ad_data = json.load(f)
    with open('playlist.json', 'r') as f: play_data = json.load(f)

    islamic_date = get_islamic_date()
    logo_url = "https://i.ibb.co/v2yPCQT/file-00000000305071fa945b58b012ac072b.png"
    
    # Base Inputs
    inputs = ""
    for v in play_data['videos']:
        inputs += f"-i {v} "
    
    # Filter Complex (Animations and Overlays)
    # 1. Scrolling Bar (Bottom)
    # 2. Program Info (Top Right - Animated)
    # 3. Logo & Islamic Date (Bottom Right)
    
    filter_complex = (
        f"[0:v]pad=iw:ih+40:0:0:black[v1]; " # Space for bar
        f"[v1]drawbox=y=ih-40:color=blue@0.8:width=iw:height=40:t=fill[v2]; " # Blue Bar
        f"[v2]drawtext=text='{bar_data['text']}':x=w-mod(t*100\,w+tw):y=h-30:fontcolor=white:fontsize=24[v3]; " # Scroll
        f"movie=logo.png[logo]; [v3][logo]overlay=main_w-160:main_h-120[v4]; " # Logo
        f"[v4]drawtext=text='{islamic_date}':x=main_w-150:y=main_h-35:fontcolor=yellow:fontsize=18[v5]; " # Date
        f"[v5]drawtext=text='NOW\: {prog_data['now']}':x=w-200:y=20+20*sin(t):fontcolor=white:fontsize=22:box=1:boxcolor=black@0.5[v_final]" # Animated Program
    )
    
    # Add Ads logic if status is 'on'
    input_source = play_data['videos'][0] # Simplified for example
    if ad_data['status'] == "on":
        input_source = ad_data['ad_url']

    command = f"ffmpeg -re -i {input_source} -i {logo_url} -filter_complex \"{filter_complex}\" " \
              f"-vcodec libx264 -preset veryfast -maxrate 3000k -bufsize 6000k " \
              f"-f hls -hls_time 4 -hls_list_size 10 -hls_flags delete_segments live/index.m3u8"
    
    return command

if __name__ == "__main__":
    print(generate_ffmpeg_command())
