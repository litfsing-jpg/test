#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сбор РЕАЛЬНЫХ данных из TikTok
Использует TikTokApi для получения публичных данных
"""

import csv
import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from TikTokApi import TikTokApi
except ImportError:
    print("❌ Установите библиотеку: pip install TikTokApi")
    print("   И playwright: python -m playwright install")
    exit(1)


class TikTokDataCollector:
    """Сборщик данных из TikTok"""

    def __init__(self):
        self.api = None

    async def init_api(self):
        """Инициализация TikTok API"""
        print("🔐 Инициализация TikTok API...")

        try:
            self.api = TikTokApi()

            # MS Token не обязателен, но улучшает стабильность
            ms_token = os.environ.get("ms_token", None)

            await self.api.create_sessions(
                ms_tokens=[ms_token] if ms_token else None,
                num_sessions=1,
                sleep_after=3,
                browser=os.getenv("TIKTOK_BROWSER", "chromium")
            )

            print("   ✅ TikTok API готов!")
            return True

        except Exception as e:
            print(f"   ❌ Ошибка инициализации: {e}")
            return False

    def extract_username_from_url(self, url: str) -> Optional[str]:
        """Извлекает username из TikTok URL"""

        # Формат: tiktok.com/@username
        if 'tiktok.com/@' in url:
            username = url.split('tiktok.com/@')[-1].split('/')[0].split('?')[0]
            return username

        return None

    async def get_user_info(self, username: str) -> Optional[Dict]:
        """Получает информацию о пользователе"""

        try:
            user = self.api.user(username)
            user_data = await user.info()

            return {
                'username': username,
                'followers': user_data.get('stats', {}).get('followerCount', 0),
                'following': user_data.get('stats', {}).get('followingCount', 0),
                'likes': user_data.get('stats', {}).get('heartCount', 0),
                'video_count': user_data.get('stats', {}).get('videoCount', 0),
                'nickname': user_data.get('nickname', username)
            }

        except Exception as e:
            print(f"   ❌ Ошибка получения данных пользователя @{username}: {e}")
            return None

    async def get_user_videos(self, username: str, count: int = 30, days: int = 30) -> List[Dict]:
        """
        Получает видео пользователя за последние N дней

        Args:
            username: TikTok username
            count: Сколько видео запросить
            days: За сколько дней собирать статистику

        Returns:
            Список видео за указанный период
        """

        try:
            user = self.api.user(username)

            # Дата начала периода (30 дней назад)
            cutoff_date = datetime.now() - timedelta(days=days)

            videos_data = []
            video_count = 0

            async for video in user.videos(count=count):
                try:
                    video_dict = video.as_dict

                    # Получаем дату публикации
                    create_time = video_dict.get('createTime', 0)
                    video_date = datetime.fromtimestamp(create_time)

                    # Пропускаем старые видео
                    if video_date < cutoff_date:
                        continue

                    # Извлекаем статистику
                    stats = video_dict.get('stats', {})

                    videos_data.append({
                        'id': video_dict.get('id'),
                        'desc': video_dict.get('desc', ''),
                        'view_count': stats.get('playCount', 0),
                        'like_count': stats.get('diggCount', 0),
                        'comment_count': stats.get('commentCount', 0),
                        'share_count': stats.get('shareCount', 0),
                        'created_at': video_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'days_old': (datetime.now() - video_date).days
                    })

                    video_count += 1

                    # Ограничиваем количество
                    if video_count >= count:
                        break

                except Exception as e:
                    # Пропускаем проблемные видео
                    continue

            return videos_data

        except Exception as e:
            print(f"   ❌ Ошибка получения видео: {e}")
            return []

    def calculate_viral_metrics(self, videos: List[Dict], followers: int) -> Dict:
        """Рассчитывает метрики вирусности"""

        if not videos or followers == 0:
            return {
                'avg_views': 0,
                'max_views': 0,
                'avg_likes': 0,
                'viral_coefficient': 0.0,
                'videos_count': 0,
                'today_video_views': None,
                'today_video_date': None
            }

        views_list = [v['view_count'] for v in videos if v['view_count'] > 0]
        likes_list = [v['like_count'] for v in videos]

        if not views_list:
            views_list = [0]

        avg_views = sum(views_list) / len(views_list)
        max_views = max(views_list) if views_list else 0
        avg_likes = sum(likes_list) / len(likes_list) if likes_list else 0

        # Вирусный коэффициент
        viral_coef = avg_views / followers if followers > 0 else 0

        # Ищем видео за сегодня
        today_video_views = None
        today_video_date = None

        for video in videos:
            if video.get('days_old') == 0:
                today_video_views = video['view_count']
                today_video_date = video['created_at']
                break

        return {
            'avg_views': int(avg_views),
            'max_views': int(max_views),
            'avg_likes': int(avg_likes),
            'viral_coefficient': round(viral_coef, 2),
            'videos_count': len(videos),
            'today_video_views': today_video_views,
            'today_video_date': today_video_date
        }

    def format_number(self, num: int) -> str:
        """Форматирует число"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.0f}K"
        return str(num)

    def get_trend(self, viral_coefficient: float) -> tuple:
        """Определяет тренд"""
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


async def collect_tiktok_data(input_csv: str, output_csv: str):
    """Собирает данные для всех TikTok аккаунтов из CSV"""

    collector = TikTokDataCollector()

    # Инициализация API
    if not await collector.init_api():
        print("\n❌ Не удалось инициализировать TikTok API")
        return

    # Читаем входной файл
    tiktok_accounts = []
    other_accounts = []

    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        for row in reader:
            if row.get('Платформа') == 'TikTok':
                tiktok_accounts.append(row)
            else:
                other_accounts.append(row)

    print(f"\n📊 Найдено TikTok аккаунтов: {len(tiktok_accounts)}")
    print(f"📊 Других платформ: {len(other_accounts)}")
    print(f"⏳ Начинаю сбор данных...\n")

    updated_accounts = []
    success_count = 0
    failed_count = 0

    for i, account in enumerate(tiktok_accounts, 1):
        name = account.get('Имя', 'Unknown')
        url = account.get('Ссылка', '')

        print(f"[{i}/{len(tiktok_accounts)}] {name}")
        print(f"   URL: {url}")

        # Извлекаем username
        username = collector.extract_username_from_url(url)

        if not username:
            print(f"   ❌ Не удалось извлечь username из URL")
            failed_count += 1
            updated_accounts.append(account)
            await asyncio.sleep(2)
            continue

        print(f"   👤 Username: @{username}")

        # Получаем информацию о пользователе
        user_info = await collector.get_user_info(username)

        if not user_info:
            print(f"   ❌ Не удалось получить информацию")
            failed_count += 1
            updated_accounts.append(account)
            await asyncio.sleep(2)
            continue

        print(f"   👥 Подписчики: {collector.format_number(user_info['followers'])}")

        # Получаем видео за последние 30 дней
        videos = await collector.get_user_videos(username, count=30, days=30)
        print(f"   🎬 Найдено видео за последний месяц: {len(videos)}")

        if not videos:
            print(f"   ⚠️  Нет видео")
            # Обновляем хотя бы подписчиков
            account['Аудитория'] = collector.format_number(user_info['followers'])
            updated_accounts.append(account)
            await asyncio.sleep(2)
            continue

        # Рассчитываем метрики
        metrics = collector.calculate_viral_metrics(videos, user_info['followers'])

        if metrics['videos_count'] > 0:
            # Показываем период видео
            oldest_video = max([v['days_old'] for v in videos])
            newest_video = min([v['days_old'] for v in videos])
            print(f"   📅 Период: {oldest_video}-{newest_video} дней назад")
            print(f"   📊 Средние просмотры: {collector.format_number(metrics['avg_views'])}")
            print(f"   💖 Средние лайки: {collector.format_number(metrics['avg_likes'])}")
            print(f"   🔥 Коэффициент: {metrics['viral_coefficient']}x")

        # Обновляем данные
        trend, trend_value = collector.get_trend(metrics['viral_coefficient'])

        account['Аудитория'] = collector.format_number(user_info['followers'])
        account['Формат_видео'] = 'TikTok'
        account['Просмотры_последнего'] = metrics['max_views']
        account['Просмотры_последнего_форматир'] = collector.format_number(metrics['max_views'])
        account['Средние_просмотры'] = metrics['avg_views']
        account['Средние_просмотры_форматир'] = collector.format_number(metrics['avg_views'])
        account['Коэффициент_вирусности'] = metrics['viral_coefficient']
        account['Видео_в_месяц'] = metrics['videos_count']
        account['Последнее_обновление'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        account['Тренд'] = trend
        account['Тренд_значение'] = trend_value

        # Добавляем видео за сегодня
        if metrics['today_video_views'] is not None:
            account['Рилс_сегодня'] = metrics['today_video_views']
            account['Рилс_сегодня_форматир'] = collector.format_number(metrics['today_video_views'])
            account['Дата_последнего_рилса'] = metrics['today_video_date']
        else:
            account['Рилс_сегодня'] = ''
            account['Рилс_сегодня_форматир'] = '-'
            account['Дата_последнего_рилса'] = ''

        updated_accounts.append(account)
        success_count += 1

        print(f"   ✅ Обновлено!\n")

        # Задержка между запросами
        await asyncio.sleep(3)

    # Закрываем API
    await collector.api.close()

    # Сохраняем результаты
    all_data = updated_accounts + other_accounts

    fieldnames = [
        'Имя', 'Никнейм/Название', 'Платформа', 'Ссылка', 'Аудитория', 'Описание',
        'Формат_видео', 'Просмотры_последнего', 'Просмотры_последнего_форматир',
        'Средние_просмотры', 'Средние_просмотры_форматир', 'Коэффициент_вирусности',
        'Видео_в_месяц', 'Последнее_обновление', 'Тренд', 'Тренд_значение',
        'Рилс_сегодня', 'Рилс_сегодня_форматир', 'Дата_последнего_рилса'
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
    print(f"   - Ошибок/пропущено: {failed_count}")
    print(f"   - Результат сохранен в: {output_csv}")
    print("=" * 80)


async def main():
    """Главная функция"""

    print("=" * 80)
    print("📱 СБОР ДАННЫХ ИЗ TIKTOK")
    print("=" * 80)
    print()

    # Запускаем сбор данных
    await collect_tiktok_data(
        input_csv='fitness_trainers_viral.csv',
        output_csv='fitness_trainers_viral_tiktok.csv'
    )


if __name__ == '__main__':
    asyncio.run(main())
