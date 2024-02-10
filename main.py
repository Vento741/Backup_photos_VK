import json
from tqdm import tqdm
from io import BytesIO
from yadisk import YaDisk
import requests

# Файл с токенами VK и Яндекс.Диск
def read_tokens(file_path='tokens.txt'):
    with open(file_path, 'r') as file:
        tokens = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in file.readlines()}
    return tokens


# Функция для получения максимального размера изображения
def get_max_size(photo_sizes):
    return max(photo_sizes, key=lambda x: x['type'])


# Функция для получения информации о фотографиях
def get_vk_photos(user_id, access_token, count=5, album_id='profile'):
    url = "https://api.vk.com/method/photos.get"
    params = {
        "user_id": user_id,
        "access_token": access_token,
        "v": "5.199",
        "album_id": album_id,
        "count": count,
        "extended": 1,
    }

    # Отправляем GET-запрос
    response = requests.get(url, params=params)
    data = response.json()

    # Проверяем, что запрос выполнен успешно
    if 'error' in data:
        raise Exception(f"Ошибка VK API: {data['error']['error_msg']}")

    photos = []

    # Формируем список словарей с информацией о фотографиях
    for item in data['response']['items']:
        max_size = get_max_size(item['sizes'])
        likes_count = item['likes']['count']
        photo_info = {
            "file_name": f"{likes_count}_{item['date']}.jpg",
            "size": max_size['type'],
            "url": max_size['url'],
        }
        photos.append(photo_info)

    return photos


# Функция для загрузки файлов на Яндекс.Диск
def upload_to_yandex_disk(yandex_token, folder, file_name, file_url):
    y = YaDisk(token=yandex_token)

    # Проверяем, есть ли уже такая папка
    if not y.exists(folder):
        print(f" Создание папки: {folder}")
        y.mkdir(folder)

    file_path = f'{folder}/{file_name}'

    # Проверяем, есть ли уже такой файл
    if y.exists(file_path):
        print(f"Файл {file_path} уже существует. Пропуск.")
        return

    # Получаем файл из URL
    response = requests.get(file_url, stream=True)

    # Загружаем данные на Яндекс.Диск
    y.upload(BytesIO(response.content), file_path)


# Основная функция
def main():
    tokens = read_tokens()

    # Запрашиваем user_id у пользователя
    user_id = input("Введите user_id VK: ")

    # Ввод пользователя
    album_id = input("Введите ID альбома VK (по умолчанию 'profile'): ")
    if not album_id:
        album_id = 'profile'

    # Запрашиваем количество фотографий
    count = int(input("Введите количество фотографий (по умолчанию 5): ") or 5)
    # Получаем информацию о фотографиях
    vk_photos = get_vk_photos(user_id, tokens.get('access_token'), count=count, album_id=album_id)

    # Пытаемся прочитать текущий JSON файл, если он существует
    try:
        with open('photo_info.json', 'r') as json_file:
            existing_photos = json.load(json_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        existing_photos = []

    # Формируем множество уникальных идентификаторов фотографий
    existing_ids = {photo['url'] for photo in existing_photos}

    # Добавляем новую информацию в JSON только для уникальных фотографий
    for photo in vk_photos:
        if photo['url'] not in existing_ids:
            existing_photos.append(photo)
            existing_ids.add(photo['url'])

    # Записываем информацию о фотографиях в JSON
    with open('photo_info.json', 'w') as json_file:
        json.dump(existing_photos, json_file, indent=2)

    # Запрашиваем токен Яндекс.Диска у пользователя
    yandex_token = input("Введите токен Яндекс.Диска: ")

    # Загружаем файлы на Яндекс.Диск
    folder = 'vk_photos'
    for photo in tqdm(vk_photos, desc='Uploading photos', unit='photo'):
        upload_to_yandex_disk(yandex_token, folder, photo['file_name'], photo['url'])


if __name__ == "__main__":
    main()