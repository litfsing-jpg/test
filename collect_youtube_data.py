#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сбор реальных данных о фитнес-блогерах через YouTube Data API v3
"""

import csv
import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ Установите библиотеку requests: pip install requests")
    exit(1)


class YouTubeDataCollector:
    """Сборщик данных с YouTube Data API v3"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.quota_used = 0
        self.quota_limit = 10000  # Дневной лимит

    def extract_channel_id(self, url: str) -> Optional[str]:
        """Извлекает ID канала из различных форматов YouTube URL"""

        # Формат: youtube.com/channel/UCxxxxx
        if '/channel/' in url:
            return url.split('/channel/')[-1].split('/')[0].split('?')[0]

        # Формат: youtube.com/@username - нужен дополнительный запрос
        if '/@' in url:
            username = url.split('/@')[-1].split('/')[0].split('?')[0]
            return self.get_channel_id_by_username(username)

        # Формат: youtube.com/c/customname - устарел, нужен поиск
        if '/c/' in url:
            custom_name = url.split('/c/')[-1].split('/')[0].split('?')[0]
            return self.get_channel_id_by_custom_name(custom_name)

        return None

    def get_channel_id_by_username(self, username: str) -> Optional[str]:
        """Получает ID канала по @username"""

        endpoint = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'q': username,
            'type': 'channel',
            'maxResults': 1,
            'key': self.api_key
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            self.quota_used += 100  # search запрос стоит 100 единиц

            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    return data['items'][0]['snippet']['channelId']
            elif response.status_code == 403:
                print(f"❌ Квота API исчерпана или ключ недействителен")
                return None
        except Exception as e:
            print(f"❌ Ошибка при поиске @{username}: {e}")

        return None

    def get_channel_id_by_custom_name(self, custom_name: str) -> Optional[str]:
        """Получает ID канала по старому custom URL (/c/)"""
        return self.get_channel_id_by_username(custom_name)

    def get_channel_stats(self, channel_id: str) -> Optional[Dict]:
        """Получает статистику канала"""

        endpoint = f"{self.base_url}/channels"
        params = {
            'part': 'statistics,snippet',
            'id': channel_id,
            'key': self.api_key
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            self.quota_used += 3  # channels запрос стоит 3 единицы (part=statistics,snippet)

            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    item = data['items'][0]
                    stats = item.get('statistics', {})
                    snippet = item.get('snippet', {})

                    return {
                        'subscribers': int(stats.get('subscriberCount', 0)),
                        'total_views': int(stats.get('viewCount', 0)),
                        'video_count': int(stats.get('videoCount', 0)),
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', '')
                    }
            elif response.status_code == 403:
                print(f"❌ Квота API исчерпана")
                return None
        except Exception as e:
            print(f"❌ Ошибка при получении статистики канала {channel_id}: {e}")

        return None

    def get_channel_shorts(self, channel_id: str, max_results: int = 10) -> List[Dict]:
        """Получает последние Shorts канала"""

        # Сначала получаем список видео
        endpoint = f"{self.base_url}/search"
        params = {
            'part': 'id',
            'channelId': channel_id,
            'type': 'video',
            'order': 'date',
            'maxResults': 50,  # Берем больше, чтобы отфильтровать Shorts
            'key': self.api_key
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            self.quota_used += 100  # search запрос

            if response.status_code != 200:
                return []

            data = response.json()
            video_ids = [item['id']['videoId'] for item in data.get('items', [])]

            if not video_ids:
                return []

            # Получаем детали видео
            videos_endpoint = f"{self.base_url}/videos"
            videos_params = {
                'part': 'statistics,contentDetails,snippet',
                'id': ','.join(video_ids[:50]),
                'key': self.api_key
            }

            videos_response = requests.get(videos_endpoint, params=videos_params, timeout=10)
            self.quota_used += 3  # videos запрос

            if videos_response.status_code != 200:
                return []

            videos_data = videos_response.json()
            shorts = []

            for video in videos_data.get('items', []):
                # Проверяем, является ли видео Shorts (длительность <= 60 секунд)
                duration = video.get('contentDetails', {}).get('duration', '')

                # Парсим ISO 8601 duration (PT1M5S = 1 минута 5 секунд)
                is_short = self.is_short_duration(duration)

                if is_short:
                    stats = video.get('statistics', {})
                    shorts.append({
                        'video_id': video['id'],
                        'title': video.get('snippet', {}).get('title', ''),
                        'views': int(stats.get('viewCount', 0)),
                        'likes': int(stats.get('likeCount', 0)),
                        'published_at': video.get('snippet', {}).get('publishedAt', '')
                    })

                if len(shorts) >= max_results:
                    break

            return shorts

        except Exception as e:
            print(f"❌ Ошибка при получении Shorts: {e}")
            return []

    def is_short_duration(self, duration: str) -> bool:
        """Проверяет, является ли видео Shorts (<=60 сек)"""

        # Формат: PT1M5S (1 минута 5 секунд) или PT45S (45 секунд)
        import re

        minutes = 0
        seconds = 0

        # Ищем минуты
        min_match = re.search(r'(\d+)M', duration)
        if min_match:
            minutes = int(min_match.group(1))

        # Ищем секунды
        sec_match = re.search(r'(\d+)S', duration)
        if sec_match:
            seconds = int(sec_match.group(1))

        total_seconds = minutes * 60 + seconds

        return total_seconds <= 60

    def calculate_viral_coefficient(self, shorts: List[Dict], subscribers: int) -> Dict:
        """Рассчитывает вирусный коэффициент на основе реальных данных"""

        if not shorts or subscribers == 0:
            return {
                'avg_views': 0,
                'max_views': 0,
                'viral_coefficient': 0.0,
                'shorts_count': 0
            }

        views_list = [s['views'] for s in shorts]
        avg_views = sum(views_list) / len(views_list)
        max_views = max(views_list)

        # Вирусный коэффициент = средние просмотры / подписчики
        viral_coef = avg_views / subscribers if subscribers > 0 else 0

        return {
            'avg_views': int(avg_views),
            'max_views': int(max_views),
            'viral_coefficient': round(viral_coef, 2),
            'shorts_count': len(shorts)
        }

    def format_number(self, num: int) -> str:
        """Форматирует число в читаемый вид"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.0f}K"
        return str(num)

    def get_trend(self, viral_coefficient: float) -> tuple:
        """Определяет тренд на основе вирусного коэффициента"""

        if viral_coefficient >= 10:
            return "🚀 Мега", "mega"
        elif viral_coefficient >= 5:
            return "🔥 Вирусно", "viral"
        elif viral_coefficient >= 2:
            return "📈 Растет", "growing"
        elif viral_coefficient >= 1:
            return "➡️ Стабильно", "stable"
        else:
            return "📉 Падает", "declining"


def collect_youtube_data(api_key: str, input_csv: str, output_csv: str):
    """Собирает данные для всех YouTube каналов из CSV"""

    collector = YouTubeDataCollector(api_key)

    # Читаем входной файл
    youtube_channels = []
    other_channels = []

    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        for row in reader:
            if row.get('Платформа') == 'YouTube':
                youtube_channels.append(row)
            else:
                other_channels.append(row)

    print(f"📊 Найдено YouTube каналов: {len(youtube_channels)}")
    print(f"📊 Других платформ: {len(other_channels)}")
    print(f"⏳ Начинаю сбор данных...\n")

    updated_channels = []
    success_count = 0
    failed_count = 0

    for i, channel in enumerate(youtube_channels, 1):
        name = channel.get('Имя', 'Unknown')
        url = channel.get('Ссылка', '')

        print(f"[{i}/{len(youtube_channels)}] {name}")
        print(f"   URL: {url}")

        # Извлекаем ID канала
        channel_id = collector.extract_channel_id(url)

        if not channel_id:
            print(f"   ❌ Не удалось получить ID канала")
            failed_count += 1
            updated_channels.append(channel)
            time.sleep(0.5)
            continue

        print(f"   ✅ ID: {channel_id}")

        # Получаем статистику канала
        stats = collector.get_channel_stats(channel_id)

        if not stats:
            print(f"   ❌ Не удалось получить статистику")
            failed_count += 1
            updated_channels.append(channel)
            time.sleep(0.5)
            continue

        print(f"   👥 Подписчики: {collector.format_number(stats['subscribers'])}")

        # Получаем Shorts
        shorts = collector.get_channel_shorts(channel_id, max_results=10)
        print(f"   🎬 Найдено Shorts: {len(shorts)}")

        # Рассчитываем метрики
        metrics = collector.calculate_viral_coefficient(shorts, stats['subscribers'])

        if metrics['shorts_count'] > 0:
            print(f"   📊 Средние просмотры: {collector.format_number(metrics['avg_views'])}")
            print(f"   🔥 Коэффициент: {metrics['viral_coefficient']}x")

        # Обновляем данные
        trend, trend_value = collector.get_trend(metrics['viral_coefficient'])

        channel['Аудитория'] = collector.format_number(stats['subscribers'])
        channel['Формат_видео'] = 'Shorts'
        channel['Просмотры_последнего'] = metrics['max_views']
        channel['Просмотры_последнего_форматир'] = collector.format_number(metrics['max_views'])
        channel['Средние_просмотры'] = metrics['avg_views']
        channel['Средние_просмотры_форматир'] = collector.format_number(metrics['avg_views'])
        channel['Коэффициент_вирусности'] = metrics['viral_coefficient']
        channel['Видео_в_месяц'] = metrics['shorts_count']
        channel['Последнее_обновление'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        channel['Тренд'] = trend
        channel['Тренд_значение'] = trend_value

        updated_channels.append(channel)
        success_count += 1

        print(f"   ✅ Обновлено! Использовано квоты: {collector.quota_used}/{collector.quota_limit}\n")

        # Задержка, чтобы не превысить rate limit
        time.sleep(1)

        # Проверка квоты
        if collector.quota_used >= collector.quota_limit * 0.9:
            print(f"⚠️  Достигнут лимит квоты API ({collector.quota_used}). Останавливаюсь.")
            break

    # Сохраняем результаты
    all_data = updated_channels + other_channels

    fieldnames = [
        'Имя', 'Никнейм/Название', 'Платформа', 'Ссылка', 'Аудитория', 'Описание',
        'Формат_видео', 'Просмотры_последнего', 'Просмотры_последнего_форматир',
        'Средние_просмотры', 'Средние_просмотры_форматир', 'Коэффициент_вирусности',
        'Видео_в_месяц', 'Последнее_обновление', 'Тренд', 'Тренд_значение'
    ]

    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_data)

    print("=" * 80)
    print("✅ СБОР ДАННЫХ ЗАВЕРШЕН!")
    print("=" * 80)
    print(f"📊 Статистика:")
    print(f"   - Успешно обновлено: {success_count}")
    print(f"   - Ошибок: {failed_count}")
    print(f"   - Использовано квоты API: {collector.quota_used}/{collector.quota_limit}")
    print(f"   - Результат сохранен в: {output_csv}")
    print("=" * 80)


if __name__ == '__main__':
    # Читаем API ключ из переменной окружения или файла
    api_key = os.getenv('YOUTUBE_API_KEY')

    if not api_key:
        # Пробуем прочитать из файла
        if os.path.exists('.youtube_api_key'):
            with open('.youtube_api_key', 'r') as f:
                api_key = f.read().strip()

    if not api_key:
        print("❌ YouTube API ключ не найден!")
        print("\nКак получить API ключ:")
        print("1. Откройте: https://console.cloud.google.com/")
        print("2. Создайте новый проект")
        print("3. Включите 'YouTube Data API v3'")
        print("4. Создайте API ключ в разделе 'Credentials'")
        print("\nЗатем создайте файл .youtube_api_key и поместите туда ключ")
        print("Или установите переменную окружения: export YOUTUBE_API_KEY='your_key'")
        exit(1)

    # Запускаем сбор данных
    collect_youtube_data(
        api_key=api_key,
        input_csv='fitness_trainers_viral.csv',
        output_csv='fitness_trainers_viral_real.csv'
    )
