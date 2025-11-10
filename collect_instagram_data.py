#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сбор РЕАЛЬНЫХ данных из Instagram Reels
Использует instagrapi для получения публичных данных
"""

import csv
import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from instagrapi import Client
except ImportError:
    print("❌ Установите библиотеку: pip install instagrapi")
    exit(1)


class InstagramReelsCollector:
    """Сборщик данных из Instagram Reels"""

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.username = username
        self.password = password
        self.logged_in = False

    def login(self):
        """Авторизация в Instagram"""

        print("🔐 Авторизация в Instagram...")

        try:
            # Попытка загрузить сессию из файла
            session_file = 'instagram_session.json'
            if os.path.exists(session_file):
                print("   📂 Загружаю сохраненную сессию...")
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password)
                print("   ✅ Сессия загружена!")
            else:
                print("   🔑 Выполняю вход...")
                self.client.login(self.username, self.password)
                # Сохраняем сессию для последующих запусков
                self.client.dump_settings(session_file)
                print("   ✅ Вход выполнен и сохранен!")

            self.logged_in = True
            return True

        except Exception as e:
            print(f"   ❌ Ошибка авторизации: {e}")
            print("\n💡 Возможные причины:")
            print("   1. Неверный логин/пароль")
            print("   2. Двухфакторная аутентификация включена (отключите)")
            print("   3. Instagram требует подтверждение входа (зайдите с телефона)")
            return False

    def extract_username_from_url(self, url: str) -> Optional[str]:
        """Извлекает username из Instagram URL"""

        # Формат: instagram.com/username или instagram.com/@username
        if 'instagram.com/' in url:
            username = url.split('instagram.com/')[-1].split('/')[0].split('?')[0]
            # Убираем @ если есть
            username = username.replace('@', '')
            return username

        return None

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Получает информацию о пользователе"""

        try:
            user_id = self.client.user_id_from_username(username)
            user_info = self.client.user_info(user_id)

            return {
                'user_id': user_id,
                'username': user_info.username,
                'full_name': user_info.full_name,
                'followers': user_info.follower_count,
                'following': user_info.following_count,
                'media_count': user_info.media_count,
                'is_private': user_info.is_private,
                'biography': user_info.biography
            }
        except Exception as e:
            print(f"   ❌ Ошибка получения данных пользователя @{username}: {e}")
            return None

    def get_user_reels(self, user_id: int, count: int = 10, days: int = 30) -> List[Dict]:
        """
        Получает Reels пользователя за последние N дней

        Args:
            user_id: ID пользователя Instagram
            count: Сколько роликов нужно вернуть (по умолчанию 10)
            days: За сколько дней собирать статистику (по умолчанию 30)

        Returns:
            Список Reels за указанный период, исключая старые закрепленные
        """

        try:
            # Запрашиваем больше роликов, чтобы точно захватить нужный период
            # instagrapi сама обрабатывает pydantic errors и возвращает то, что смогла распарсить
            clips = self.client.user_clips(user_id, amount=50)

            # Дата начала периода (30 дней назад)
            cutoff_date = datetime.now() - timedelta(days=days)

            # Собираем ВСЕ ролики с данными
            all_reels = []
            for clip in clips:
                try:
                    # Получаем дату публикации
                    clip_date = clip.taken_at.replace(tzinfo=None) if hasattr(clip.taken_at, 'tzinfo') else clip.taken_at

                    all_reels.append({
                        'id': clip.pk,
                        'code': clip.code,
                        'url': f"https://www.instagram.com/reel/{clip.code}/",
                        'caption': clip.caption_text if clip.caption_text else '',
                        'view_count': clip.view_count if hasattr(clip, 'view_count') else 0,
                        'like_count': clip.like_count,
                        'comment_count': clip.comment_count,
                        'play_count': clip.play_count if hasattr(clip, 'play_count') else clip.view_count,
                        'created_at': clip.taken_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'clip_date': clip_date,
                        'days_old': (datetime.now() - clip_date).days
                    })
                except Exception as e:
                    # Пропускаем проблемные ролики
                    continue

            # Фильтруем только свежие ролики (за последние N дней)
            fresh_reels = [r for r in all_reels if r['clip_date'] >= cutoff_date]

            # Сортируем по дате (новые первые) и берем топ-N
            fresh_reels.sort(key=lambda x: x['clip_date'], reverse=True)
            result_reels = fresh_reels[:count]

            # Удаляем служебное поле clip_date перед возвратом
            for r in result_reels:
                del r['clip_date']

            return result_reels

        except Exception as e:
            print(f"   ❌ Ошибка получения Reels: {e}")
            return []

    def calculate_viral_metrics(self, reels: List[Dict], followers: int) -> Dict:
        """Рассчитывает метрики вирусности"""

        if not reels or followers == 0:
            return {
                'avg_views': 0,
                'max_views': 0,
                'avg_likes': 0,
                'viral_coefficient': 0.0,
                'reels_count': 0,
                'today_reel_views': None,
                'today_reel_date': None
            }

        # Используем play_count как просмотры
        views_list = [r['play_count'] for r in reels if r['play_count'] > 0]
        likes_list = [r['like_count'] for r in reels]

        if not views_list:
            views_list = [0]

        avg_views = sum(views_list) / len(views_list)
        max_views = max(views_list) if views_list else 0
        avg_likes = sum(likes_list) / len(likes_list) if likes_list else 0

        # Вирусный коэффициент = средние просмотры / подписчики
        viral_coef = avg_views / followers if followers > 0 else 0

        # Ищем рилс за сегодня (самый свежий, 0 дней назад)
        today_reel_views = None
        today_reel_date = None

        for reel in reels:
            if reel.get('days_old') == 0:
                today_reel_views = reel['play_count']
                today_reel_date = reel['created_at']
                break

        return {
            'avg_views': int(avg_views),
            'max_views': int(max_views),
            'avg_likes': int(avg_likes),
            'viral_coefficient': round(viral_coef, 2),
            'reels_count': len(reels),
            'today_reel_views': today_reel_views,
            'today_reel_date': today_reel_date
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


def collect_instagram_data(username: str, password: str, input_csv: str, output_csv: str):
    """Собирает данные для всех Instagram аккаунтов из CSV"""

    collector = InstagramReelsCollector(username, password)

    # Авторизация
    if not collector.login():
        print("\n❌ Не удалось авторизоваться в Instagram")
        print("\n📋 Что нужно сделать:")
        print("1. Создайте отдельный Instagram аккаунт для парсинга (или используйте существующий)")
        print("2. Убедитесь что двухфакторная аутентификация ОТКЛЮЧЕНА")
        print("3. Запустите скрипт еще раз с правильными данными")
        return

    # Читаем входной файл
    instagram_accounts = []
    other_accounts = []

    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        for row in reader:
            if row.get('Платформа') == 'Instagram':
                instagram_accounts.append(row)
            else:
                other_accounts.append(row)

    print(f"\n📊 Найдено Instagram аккаунтов: {len(instagram_accounts)}")
    print(f"📊 Других платформ: {len(other_accounts)}")
    print(f"⏳ Начинаю сбор данных...\n")

    updated_accounts = []
    success_count = 0
    failed_count = 0

    for i, account in enumerate(instagram_accounts, 1):
        name = account.get('Имя', 'Unknown')
        url = account.get('Ссылка', '')

        print(f"[{i}/{len(instagram_accounts)}] {name}")
        print(f"   URL: {url}")

        # Извлекаем username
        username = collector.extract_username_from_url(url)

        if not username:
            print(f"   ❌ Не удалось извлечь username из URL")
            failed_count += 1
            updated_accounts.append(account)
            time.sleep(1)
            continue

        print(f"   👤 Username: @{username}")

        # Получаем информацию о пользователе
        user_info = collector.get_user_info(username)

        if not user_info:
            print(f"   ❌ Не удалось получить информацию")
            failed_count += 1
            updated_accounts.append(account)
            time.sleep(2)
            continue

        if user_info['is_private']:
            print(f"   ⚠️  Приватный аккаунт - пропускаем")
            failed_count += 1
            updated_accounts.append(account)
            time.sleep(2)
            continue

        print(f"   👥 Подписчики: {collector.format_number(user_info['followers'])}")

        # Получаем Reels за последние 30 дней
        reels = collector.get_user_reels(user_info['user_id'], count=10, days=30)
        print(f"   🎬 Найдено Reels за последний месяц: {len(reels)}")

        if not reels:
            print(f"   ⚠️  Нет Reels")
            # Обновляем хотя бы подписчиков
            account['Аудитория'] = collector.format_number(user_info['followers'])
            updated_accounts.append(account)
            time.sleep(2)
            continue

        # Рассчитываем метрики
        metrics = collector.calculate_viral_metrics(reels, user_info['followers'])

        if metrics['reels_count'] > 0:
            # Показываем период роликов
            oldest_reel = max([r['days_old'] for r in reels])
            newest_reel = min([r['days_old'] for r in reels])
            print(f"   📅 Период: {oldest_reel}-{newest_reel} дней назад")
            print(f"   📊 Средние просмотры: {collector.format_number(metrics['avg_views'])}")
            print(f"   💖 Средние лайки: {collector.format_number(metrics['avg_likes'])}")
            print(f"   🔥 Коэффициент: {metrics['viral_coefficient']}x")

        # Обновляем данные
        trend, trend_value = collector.get_trend(metrics['viral_coefficient'])

        account['Аудитория'] = collector.format_number(user_info['followers'])
        account['Формат_видео'] = 'Reels'
        account['Просмотры_последнего'] = metrics['max_views']
        account['Просмотры_последнего_форматир'] = collector.format_number(metrics['max_views'])
        account['Средние_просмотры'] = metrics['avg_views']
        account['Средние_просмотры_форматир'] = collector.format_number(metrics['avg_views'])
        account['Коэффициент_вирусности'] = metrics['viral_coefficient']
        account['Видео_в_месяц'] = metrics['reels_count']
        account['Последнее_обновление'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        account['Тренд'] = trend
        account['Тренд_значение'] = trend_value

        # Добавляем рилс за сегодня
        if metrics['today_reel_views'] is not None:
            account['Рилс_сегодня'] = metrics['today_reel_views']
            account['Рилс_сегодня_форматир'] = collector.format_number(metrics['today_reel_views'])
            account['Дата_последнего_рилса'] = metrics['today_reel_date']
        else:
            account['Рилс_сегодня'] = ''
            account['Рилс_сегодня_форматир'] = '-'
            account['Дата_последнего_рилса'] = ''

        updated_accounts.append(account)
        success_count += 1

        print(f"   ✅ Обновлено!\n")

        # Задержка между запросами (важно!)
        time.sleep(3)

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


if __name__ == '__main__':
    print("=" * 80)
    print("📸 СБОР ДАННЫХ ИЗ INSTAGRAM REELS")
    print("=" * 80)
    print()

    # Получаем учетные данные Instagram
    ig_username = os.getenv('INSTAGRAM_USERNAME')
    ig_password = os.getenv('INSTAGRAM_PASSWORD')

    if not ig_username or not ig_password:
        # Пробуем прочитать из файла
        if os.path.exists('.instagram_credentials'):
            with open('.instagram_credentials', 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 2:
                    ig_username = lines[0].strip()
                    ig_password = lines[1].strip()

    if not ig_username or not ig_password:
        print("❌ Instagram учетные данные не найдены!")
        print("\nСоздайте файл .instagram_credentials с двумя строками:")
        print("  Строка 1: ваш Instagram логин")
        print("  Строка 2: ваш Instagram пароль")
        print("\nИли установите переменные окружения:")
        print("  export INSTAGRAM_USERNAME='your_username'")
        print("  export INSTAGRAM_PASSWORD='your_password'")
        print("\n⚠️  ВАЖНО:")
        print("  - Рекомендуется использовать отдельный аккаунт")
        print("  - Отключите двухфакторную аутентификацию")
        print("  - Не используйте основной аккаунт!")
        exit(1)

    # Запускаем сбор данных
    collect_instagram_data(
        username=ig_username,
        password=ig_password,
        input_csv='fitness_trainers_viral.csv',
        output_csv='fitness_trainers_viral_real.csv'
    )
