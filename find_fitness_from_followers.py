#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск Instagram аккаунтов фитнес-тренеров через подписки существующих блогеров
Собирает 500 аккаунтов с 5K+ подписчиками
"""

import csv
import time
import os
from typing import Dict, Set

try:
    from instagrapi import Client
except ImportError:
    print("❌ Установите библиотеку: pip install instagrapi")
    exit(1)


class FitnessAccountFinderFromFollowers:
    """Поиск фитнес-аккаунтов через подписки существующих блогеров"""

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.username = username
        self.password = password
        self.found_accounts = {}  # username -> follower_count
        self.processed_usernames = set()

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

    def get_following_accounts(self, username: str, amount: int = 100):
        """
        Получить подписки пользователя

        Args:
            username: Instagram username
            amount: Сколько подписок получить
        """

        print(f"\n🔍 Анализирую подписки @{username}...")

        try:
            # Получаем user_id
            user_id = self.client.user_id_from_username(username)

            # Получаем подписки
            following = self.client.user_following(user_id, amount=amount)

            print(f"   📊 Найдено подписок: {len(following)}")

            found_count = 0

            for user_id, user_info in following.items():
                try:
                    username_found = user_info.username

                    # Пропускаем уже обработанных
                    if username_found in self.processed_usernames:
                        continue

                    self.processed_usernames.add(username_found)

                    # Получаем полную информацию
                    full_user_info = self.client.user_info(user_id)

                    followers = full_user_info.follower_count

                    # Фильтр: от 5000 подписчиков
                    if followers >= 5000 and followers <= 500000:  # Не берем слишком больших (скорее всего знаменитости)
                        # Проверяем что это не приватный аккаунт
                        if not full_user_info.is_private:
                            # Проверяем что это живой аккаунт
                            if full_user_info.media_count > 10:
                                # Проверяем что в биографии есть ключевые слова
                                bio = (full_user_info.biography or '').lower()
                                keywords = ['фитнес', 'тренер', 'fitness', 'trainer', 'coach', 'gym', 'workout', 'спорт']

                                if any(keyword in bio for keyword in keywords):
                                    self.found_accounts[username_found] = followers
                                    found_count += 1
                                    print(f"   ✅ @{username_found}: {self.format_number(followers)} подписчиков")

                    # Задержка
                    time.sleep(1)

                except Exception as e:
                    # Пропускаем проблемные аккаунты
                    continue

            print(f"   🎯 Найдено подходящих: {found_count}")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

    def format_number(self, num: int) -> str:
        """Форматирует число"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.0f}K"
        return str(num)

    def find_accounts(self, seed_accounts: list, target_count: int = 500):
        """
        Основная функция поиска

        Args:
            seed_accounts: Список начальных аккаунтов фитнес-блогеров
            target_count: Сколько аккаунтов нужно найти
        """

        print("=" * 80)
        print("🔍 ПОИСК ФИТНЕС-АККАУНТОВ ЧЕРЕЗ ПОДПИСКИ")
        print("=" * 80)
        print(f"🎯 Цель: {target_count} аккаунтов с 5-500K подписчиками")
        print(f"📋 Критерии:")
        print(f"   - 5000-500000 подписчиков")
        print(f"   - Не приватный аккаунт")
        print(f"   - Есть посты (10+)")
        print(f"   - В био есть ключевые слова фитнес/тренер")
        print()

        for seed_account in seed_accounts:
            # Проверяем достигли ли цели
            if len(self.found_accounts) >= target_count:
                print(f"\n🎉 Достигнута цель: {len(self.found_accounts)} аккаунтов!")
                break

            # Анализируем подписки
            self.get_following_accounts(seed_account, amount=200)

            # Показываем прогресс
            progress = (len(self.found_accounts) / target_count) * 100
            print(f"\n📊 Прогресс: {len(self.found_accounts)}/{target_count} ({progress:.1f}%)")

            # Задержка между аккаунтами
            time.sleep(5)

        return self.found_accounts

    def save_to_excel(self, filename: str = 'имена.csv'):
        """Сохранение в CSV"""

        print(f"\n💾 Сохранение в {filename}...")

        # Сортируем по подписчикам
        sorted_accounts = sorted(
            self.found_accounts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Сохраняем
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Instagram Username', 'Количество подписчиков'])

            for username, followers in sorted_accounts:
                writer.writerow([f'@{username}', followers])

        print(f"✅ Сохранено {len(sorted_accounts)} аккаунтов в {filename}")
        print(f"\n🏆 Топ-10 по подписчикам:")
        for i, (username, followers) in enumerate(sorted_accounts[:10], 1):
            print(f"   {i}. @{username}: {self.format_number(followers)}")


def main():
    """Главная функция"""

    # Загружаем существующих блогеров как seed
    seed_accounts = []

    # Читаем из нашей существующей базы
    if os.path.exists('fitness_trainers_viral.csv'):
        with open('fitness_trainers_viral.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Платформа') == 'Instagram':
                    url = row.get('Ссылка', '')
                    if 'instagram.com/' in url:
                        username = url.split('instagram.com/')[-1].split('/')[0].split('?')[0].replace('@', '')
                        seed_accounts.append(username)

    print(f"📋 Загружено {len(seed_accounts)} начальных аккаунтов")

    # Получаем учетные данные
    ig_username = os.getenv('INSTAGRAM_USERNAME')
    ig_password = os.getenv('INSTAGRAM_PASSWORD')

    if not ig_username or not ig_password:
        if os.path.exists('.instagram_credentials'):
            with open('.instagram_credentials', 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 2:
                    ig_username = lines[0].strip()
                    ig_password = lines[1].strip()

    if not ig_username or not ig_password:
        print("❌ Instagram учетные данные не найдены!")
        exit(1)

    # Создаем поисковик
    finder = FitnessAccountFinderFromFollowers(ig_username, ig_password)

    # Авторизуемся
    if not finder.login():
        exit(1)

    # Ищем аккаунты
    accounts = finder.find_accounts(seed_accounts, target_count=500)

    # Сохраняем
    finder.save_to_excel('имена.csv')

    print("\n" + "=" * 80)
    print("✅ ПОИСК ЗАВЕРШЕН!")
    print("=" * 80)
    print(f"📊 Найдено аккаунтов: {len(accounts)}")
    print(f"💾 Сохранено в: имена.csv")


if __name__ == '__main__':
    main()
