import requests
from tqdm import tqdm
import os
from bs4 import BeautifulSoup
import subprocess
from uuid import uuid4
import random
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.all import colorx
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
from PIL import Image  # Импортируем Image из Pillow

def clear_directory(folder_name):
    """ Удаляет все файлы в указанной папке. """
    for item in os.listdir(folder_name):
        item_path = os.path.join(folder_name, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
            print(f"Removed {item_path}")

def ensure_folder_exists(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    else:
        clear_directory(folder_name)  # Очищаем папку перед загрузкой
    print(f"Folder '{folder_name}' ready")

def download(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.4',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://tmate.cc',
        'Connection': 'keep-alive',
        'Referer': 'https://tmate.cc/',
    }

    # Сохраняем видео в папку 'video'
    ensure_folder_exists('video')
    file_name = link.split('/')[-1]
    save_path = os.path.join('video', f'{file_name}.mp4')

    try:
        with requests.Session() as s:
            response = s.get("https://tmate.cc/", headers=headers, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            token = soup.find("input", {"name": "token"})["value"]
            data = {'url': link, 'token': token}
            response = s.post('https://tmate.cc/download', headers=headers, data=data, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            download_link = soup.find(class_="downtmate-right is-desktop-only right").find("a")["href"]
            response = s.get(download_link, stream=True, headers=headers, verify=False)
            
            # Процесс загрузки файла
            with open(save_path, 'wb') as video_file, tqdm(
                total=int(response.headers.get('content-length', 0)),
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                bar_format='{percentage:3.0f}%|{bar:20}{r_bar}{desc}',
                colour='green',
                desc=f"[{file_name}]"
            ) as progress_bar:
                for data in response.iter_content(chunk_size=1024):
                    size = video_file.write(data)
                    progress_bar.update(size)
            print(f"Downloaded {file_name}")

    except Exception as e:
        print(f"Error downloading {link}: {e}")

def remove_metadata_and_uniquify(directory='video'):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            original_path = os.path.join(directory, filename)
            unique_filename = f"{filename.rsplit('.', 1)[0]}_{uuid4().hex}.{filename.rsplit('.', 1)[1]}"
            output_path = os.path.join(directory, unique_filename)

            clip = VideoFileClip(original_path)
            resolution_options = [(720, 1280), (1080, 1920), (540, 960)]
            selected_resolution = random.choice(resolution_options)
            fps_options = [24, 25, 30]
            selected_fps = random.choice(fps_options)
            clip_resized = clip.resize(newsize=selected_resolution).set_fps(selected_fps)

            # Применяем изменения насыщенности
            clip_color_adjusted = clip_resized.fx(colorx, 0.95)

            # Добавляем текстовый водяной знак внизу
            fontsize = 24
            text_y_position = selected_resolution[1] - fontsize - 10  # 10 pixels from bottom
            txt_clip = TextClip("BreezeGO", fontsize=fontsize, color='white', font='Arial', size=clip_resized.size) \
                .set_position(('center', text_y_position)) \
                .set_duration(clip.duration)
            video = CompositeVideoClip([clip_color_adjusted, txt_clip])

            # Добавляем рамку
            video = video.margin(top=20, left=20, right=20, bottom=20, color=(0,0,0))

            # Применяем микро изменения аудио
            video = video.fx(audio_fadein, 0.1).fx(audio_fadeout, 0.1)

            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            os.remove(original_path)
            print(f"Processed and removed metadata: {original_path} -> {output_path}")

if __name__ == '__main__':
    clear_directory('video')
    # Запрашиваем ссылку на видео у пользователя
    video_url = input("Please enter the video URL: ")
    download(video_url)
    remove_metadata_and_uniquify()
