#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск Instagram аккаунтов фитнес-тренеров через хэштеги
Собирает 500 аккаунтов с 5K+ подписчиками
"""

import csv
import time
import os
from typing import Dict, Set
from datetime import datetime

try:
    from instagrapi import Client
except ImportError:
    print("❌ Установите библиотеку: pip install instagrapi")
    exit(1)


class FitnessAccountFinder:
    """Поиск фитнес-аккаунтов через хэштеги"""

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.username = username
        self.password = password
        self.found_accounts = {}  # username -> follower_count
        self.processed_usernames = set()  # Чтобы избежать дубликатов

    def login(self):
        """Авторизация в Instagram"""
        print("🔐 Авторизация в Instagram...")

        try:
            session_file = 'instagram_session.json'
            if os.path.exists(session_file):
                print("   📂 Загружаю сохраненную сессию...")
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password)
                print("   ✅ Сессия загружена!")
            else:
                print("   🔑 Выполняю вход...")
                self.client.login(self.username, self.password)
                self.client.dump_settings(session_file)
                print("   ✅ Вход выполнен и сохранен!")

            return True

        except Exception as e:
            print(f"   ❌ Ошибка авторизации: {e}")
            return False

    def search_by_hashtag(self, hashtag: str, amount: int = 100) -> Set[str]:
        """
        Поиск аккаунтов через хэштег

        Args:
            hashtag: Хэштег для поиска (без #)
            amount: Сколько постов проверить

        Returns:
            Set юзернеймов найденных авторов
        """

        print(f"\n🔍 Поиск по #{hashtag}...")
        found_users = set()

        try:
            # Получаем свежие посты по хэштегу
            medias = self.client.hashtag_medias_recent(hashtag, amount=amount)

            print(f"   📊 Найдено постов: {len(medias)}")

            for media in medias:
                try:
                    username = media.user.username

                    # Пропускаем уже обработанных
                    if username in self.processed_usernames:
                        continue

                    self.processed_usernames.add(username)

                    # Получаем полную информацию о пользователе
                    user_info = self.client.user_info(media.user.pk)

                    followers = user_info.follower_count

                    # Фильтр: от 5000 подписчиков
                    if followers >= 5000:
                        # Проверяем что это не приватный аккаунт
                        if not user_info.is_private:
                            # Проверяем что это живой аккаунт (есть посты)
                            if user_info.media_count > 10:
                                self.found_accounts[username] = followers
                                found_users.add(username)
                                print(f"   ✅ @{username}: {self.format_number(followers)} подписчиков")

                    # Задержка чтобы не забанили
                    time.sleep(1)

                except Exception as e:
                    # Пропускаем проблемные аккаунты
                    continue

            print(f"   🎯 Найдено подходящих: {len(found_users)}")

        except Exception as e:
            print(f"   ❌ Ошибка поиска по #{hashtag}: {e}")

        return found_users

    def format_number(self, num: int) -> str:
        """Форматирует число в читаемый вид"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.0f}K"
        return str(num)

    def find_accounts(self, target_count: int = 500):
        """
        Основная функция поиска аккаунтов

        Args:
            target_count: Сколько аккаунтов нужно найти
        """

        print("=" * 80)
        print("🔍 ПОИСК ФИТНЕС-АККАУНТОВ В INSTAGRAM")
        print("=" * 80)
        print(f"🎯 Цель: {target_count} аккаунтов с 5K+ подписчиками")
        print(f"📋 Критерии:")
        print(f"   - Минимум 5000 подписчиков")
        print(f"   - Не приватный аккаунт")
        print(f"   - Есть посты (10+)")
        print()

        # Список хэштегов для поиска
        hashtags = [
            # Русские
            'фитнестренер',
            'фитнесмосква',
            'фитнесмодель',
            'фитнесбикини',
            'фитнесонлайн',
            'тренерпофитнесу',
            'персональныйтренер',
            'онлайнтренер',
            'фитнестренировки',
            'фитнесинструктор',

            # Английские
            'fitnesstrainer',
            'fitnesscoach',
            'personaltrainer',
            'fitnessmodel',
            'fitnessmotivation',
            'gymtrainer',
            'onlinecoach',
            'fitnesspro',
            'fitnesslife',
            'workoutcoach'
        ]

        for hashtag in hashtags:
            # Проверяем достигли ли цели
            if len(self.found_accounts) >= target_count:
                print(f"\n🎉 Достигнута цель: {len(self.found_accounts)} аккаунтов!")
                break

            # Ищем по хэштегу
            self.search_by_hashtag(hashtag, amount=50)

            # Показываем прогресс
            progress = (len(self.found_accounts) / target_count) * 100
            print(f"\n📊 Прогресс: {len(self.found_accounts)}/{target_count} ({progress:.1f}%)")

            # Задержка между хэштегами
            time.sleep(5)

        return self.found_accounts

    def save_to_excel(self, filename: str = 'имена.csv'):
        """Сохранение результатов в CSV (Excel)"""

        print(f"\n💾 Сохранение в {filename}...")

        # Сортируем по количеству подписчиков (от большего к меньшему)
        sorted_accounts = sorted(
            self.found_accounts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Сохраняем в CSV с кодировкой UTF-8-BOM для Excel
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # Заголовок
            writer.writerow(['Instagram Username', 'Количество подписчиков'])

            # Данные
            for username, followers in sorted_accounts:
                writer.writerow([f'@{username}', followers])

        print(f"✅ Сохранено {len(sorted_accounts)} аккаунтов в {filename}")
        print(f"\n🏆 Топ-10 по подписчикам:")
        for i, (username, followers) in enumerate(sorted_accounts[:10], 1):
            print(f"   {i}. @{username}: {self.format_number(followers)}")


def main():
    """Главная функция"""

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
        print("\nИспользуйте файл .instagram_credentials")
        exit(1)

    # Создаем поисковик
    finder = FitnessAccountFinder(ig_username, ig_password)

    # Авторизуемся
    if not finder.login():
        exit(1)

    # Ищем 500 аккаунтов
    accounts = finder.find_accounts(target_count=500)

    # Сохраняем в Excel
    finder.save_to_excel('имена.csv')

    print("\n" + "=" * 80)
    print("✅ ПОИСК ЗАВЕРШЕН!")
    print("=" * 80)
    print(f"📊 Найдено аккаунтов: {len(accounts)}")
    print(f"💾 Сохранено в: имена.csv")
    print("\n💡 Откройте файл в Excel для просмотра результатов")


if __name__ == '__main__':
    main()
