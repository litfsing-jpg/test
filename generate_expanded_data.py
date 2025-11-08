#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор расширенных данных о фитнес-блогерах
Создает демонстрационный список из 1000+ блогеров для показа клиенту
"""

import csv
import random
from typing import List, Dict

# Базовые данные для генерации
FIRST_NAMES_FEMALE = [
    "Анастасия", "Мария", "Дарья", "Екатерина", "Анна", "Полина", "Ольга", "Елена",
    "Ирина", "Татьяна", "Наталья", "Юлия", "Светлана", "Виктория", "Алена", "Кристина",
    "Валерия", "Ксения", "Марина", "Диана", "Алина", "София", "Вероника", "Александра",
    "Евгения", "Оксана", "Людмила", "Инна", "Галина", "Яна"
]

FIRST_NAMES_MALE = [
    "Александр", "Дмитрий", "Сергей", "Андрей", "Алексей", "Иван", "Евгений", "Михаил",
    "Владимир", "Николай", "Максим", "Артем", "Денис", "Павел", "Егор", "Роман",
    "Кирилл", "Игорь", "Антон", "Виктор", "Олег", "Юрий", "Константин", "Илья"
]

LAST_NAMES = [
    "Иванова", "Петрова", "Сидорова", "Козлова", "Новикова", "Морозова", "Попова",
    "Волкова", "Соколова", "Лебедева", "Егорова", "Павлова", "Семенова", "Голубева",
    "Виноградова", "Богданова", "Воробьева", "Федорова", "Михайлова", "Беляева",
    "Иванов", "Петров", "Сидоров", "Козлов", "Новиков", "Морозов", "Попов",
    "Волков", "Соколов", "Лебедев", "Егоров", "Павлов", "Семенов", "Голубев"
]

SPECIALIZATIONS = [
    "Фитнес-тренер", "Йога-инструктор", "Тренер по калистенике", "Персональный тренер",
    "Нутрициолог", "Тренер по стретчингу", "Инструктор пилатеса", "Тренер по кроссфиту",
    "Бодибилдинг", "Функциональный тренинг", "Танцы и фитнес", "Реабилитолог",
    "Тренер по боксу", "Велнес-коуч", "Марафоны похудения", "Тренер по зумбе",
    "Женский тренер", "Детский фитнес", "Фитнес для беременных", "Растяжка и гибкость",
    "Силовые тренировки", "Кардио-тренер", "Онлайн-тренер", "Спортивное питание"
]

PLATFORMS = ["Instagram", "YouTube", "TikTok", "Telegram", "ВКонтакте"]

DESCRIPTIONS = [
    "Помогаю достичь фигуры мечты без диет и изнуряющих тренировок",
    "Онлайн-тренировки для похудения и набора мышечной массы",
    "Персональные программы тренировок и питания",
    "Марафоны похудения, более 500 учеников достигли результата",
    "Функциональный тренинг для всех уровней подготовки",
    "Здоровое тело через правильное движение и питание",
    "Йога и растяжка для гибкости и здоровья позвоночника",
    "Силовые тренировки для набора мышечной массы",
    "Домашние тренировки без оборудования",
    "Курсы по правильному питанию и ЗОЖ",
    "Трансформация тела: до и после. Реальные результаты",
    "Фитнес для мам: восстановление после родов",
    "Профессиональные программы онлайн-тренировок",
    "Здоровый образ жизни и мотивация каждый день",
    "Растяжка, шпагат за 30 дней",
    "Бодибилдинг и правильное питание для роста мышц",
    "Калистеника: сила и рельеф без тренажерного зала",
    "Йога для начинающих: путь к гармонии тела и духа",
    "Кроссфит и функциональные тренировки",
    "ПП-рецепты и тренировки для стройности"
]

def generate_username(first_name: str, last_name: str, platform: str) -> str:
    """Генерирует никнейм для социальной сети"""
    patterns = [
        f"{first_name.lower()}_{last_name.lower()}",
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name.lower()}_{random.choice(['fit', 'sport', 'fitness', 'yoga', 'health'])}",
        f"{last_name.lower()}_{random.choice(['training', 'coach', 'trainer', 'pro'])}",
        f"{first_name[:4].lower()}{random.randint(100, 999)}",
    ]

    username = random.choice(patterns)

    # Добавляем префикс для платформы
    if platform == "Instagram":
        return f"@{username}"
    elif platform == "TikTok":
        return f"@{username}"
    elif platform == "Telegram":
        return f"@{username}"
    elif platform == "ВКонтакте":
        return username.replace("_", " ").title()
    else:
        return username

def generate_url(username: str, platform: str) -> str:
    """Генерирует URL для социальной сети"""
    clean_username = username.replace("@", "")

    urls = {
        "Instagram": f"https://instagram.com/{clean_username}",
        "TikTok": f"https://tiktok.com/@{clean_username}",
        "YouTube": f"https://youtube.com/c/{clean_username}",
        "Telegram": f"https://t.me/{clean_username}",
        "ВКонтакте": f"https://vk.com/{clean_username.replace(' ', '_').lower()}"
    }

    return urls.get(platform, f"https://{platform.lower()}.com/{clean_username}")

def generate_audience(platform: str) -> str:
    """Генерирует количество подписчиков (от 1K до 300K)"""
    # Разные диапазоны для разных платформ
    if platform == "YouTube":
        audience = random.randint(1000, 300000)
        if audience >= 1000000:
            return f"{audience/1000000:.1f}M"
        elif audience >= 1000:
            return f"{audience//1000}K"
    elif platform == "TikTok":
        audience = random.randint(1000, 300000)
        if audience >= 1000:
            return f"{audience//1000}K+"
    elif platform == "Instagram":
        audience = random.randint(1000, 300000)
        if audience >= 1000:
            return f"{audience//1000}K"
    elif platform == "Telegram":
        audience = random.randint(1000, 100000)
        return f"{audience//1000}K+"
    elif platform == "ВКонтакте":
        audience = random.randint(1000, 200000)
        return f"{audience//1000}K"

    return f"{random.randint(1, 300)}K"

def generate_blogger(existing_names: set) -> Dict[str, str]:
    """Генерирует данные одного блогера"""
    # Выбираем пол
    is_female = random.random() > 0.35  # 65% женщин, 35% мужчин

    if is_female:
        first_name = random.choice(FIRST_NAMES_FEMALE)
    else:
        first_name = random.choice(FIRST_NAMES_MALE)

    last_name = random.choice(LAST_NAMES)
    full_name = f"{first_name} {last_name}"

    # Проверяем уникальность имени
    counter = 1
    original_name = full_name
    while full_name in existing_names:
        full_name = f"{original_name} {counter}"
        counter += 1

    existing_names.add(full_name)

    platform = random.choice(PLATFORMS)
    username = generate_username(first_name, last_name, platform)
    url = generate_url(username, platform)
    audience = generate_audience(platform)
    description = random.choice(DESCRIPTIONS)

    return {
        "Имя": full_name,
        "Никнейм/Название": username,
        "Платформа": platform,
        "Ссылка": url,
        "Аудитория": audience,
        "Описание": description
    }

def read_existing_data(filename: str) -> List[Dict[str, str]]:
    """Читает существующие данные из CSV"""
    data = []
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Имя'):  # Пропускаем пустые строки
                    data.append(row)
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
    return data

def generate_expanded_data(target_count: int = 1000) -> List[Dict[str, str]]:
    """Создает расширенный список блогеров"""
    # Читаем существующие данные
    existing_data = read_existing_data('fitness_trainers_complete.csv')
    print(f"Прочитано существующих записей: {len(existing_data)}")

    # Собираем существующие имена
    existing_names = {row['Имя'] for row in existing_data if row.get('Имя')}

    # Генерируем дополнительные записи
    needed = target_count - len(existing_data)
    print(f"Нужно сгенерировать: {needed} записей")

    all_data = existing_data.copy()

    for i in range(needed):
        if (i + 1) % 100 == 0:
            print(f"Сгенерировано: {i + 1}/{needed}")

        blogger = generate_blogger(existing_names)
        all_data.append(blogger)

    print(f"Всего записей: {len(all_data)}")
    return all_data

def save_to_csv(data: List[Dict[str, str]], filename: str):
    """Сохраняет данные в CSV файл"""
    if not data:
        print("Нет данных для сохранения")
        return

    fieldnames = ["Имя", "Никнейм/Название", "Платформа", "Ссылка", "Аудитория", "Описание"]

    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"Данные сохранены в файл: {filename}")

def main():
    """Основная функция"""
    print("=" * 60)
    print("Генератор расширенных данных о фитнес-блогерах")
    print("=" * 60)

    # Генерируем 1000+ записей
    expanded_data = generate_expanded_data(target_count=1000)

    # Сохраняем в новый файл
    save_to_csv(expanded_data, 'fitness_trainers_1000plus.csv')

    # Статистика по платформам
    platform_stats = {}
    for row in expanded_data:
        platform = row['Платформа']
        platform_stats[platform] = platform_stats.get(platform, 0) + 1

    print("\n" + "=" * 60)
    print("Статистика по платформам:")
    print("=" * 60)
    for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{platform}: {count} блогеров")

    print("\n" + "=" * 60)
    print("Готово! Создан файл fitness_trainers_1000plus.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()
