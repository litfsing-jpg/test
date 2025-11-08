#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram бот для уведомлений о вирусных роликах фитнес-блогеров

Требования:
pip install python-telegram-bot python-dotenv

Настройка:
1. Создайте бота через @BotFather в Telegram
2. Скопируйте токен бота
3. Создайте файл .env с содержимым: TELEGRAM_BOT_TOKEN=ваш_токен
4. Запустите: python telegram_bot.py
"""

import os
import csv
import asyncio
from datetime import datetime
from typing import List, Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Установите python-dotenv: pip install python-dotenv")

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
CHECK_INTERVAL = 30 * 60  # 30 минут

# Хранилище подписчиков
subscribers = set()

def load_viral_data() -> List[Dict]:
    """Загружает данные о блогерах из CSV"""
    data = []
    try:
        with open('fitness_trainers_viral.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    coef = float(row.get('Коэффициент_вирусности', 0))
                    if coef >= 5.0:  # Только вирусные
                        data.append({
                            'name': row['Имя'],
                            'platform': row['Платформа'],
                            'username': row['Никнейм/Название'],
                            'viral_coef': coef,
                            'views': row['Просмотры_последнего_форматир'],
                            'url': row['Ссылка']
                        })
                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        print("Файл fitness_trainers_viral.csv не найден!")

    return sorted(data, key=lambda x: x['viral_coef'], reverse=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    subscribers.add(user_id)

    await update.message.reply_text(
        "🔥 Добро пожаловать в систему мониторинга вирусных роликов!\n\n"
        "Вы подписаны на уведомления о новых вирусных роликах фитнес-блогеров.\n\n"
        "Доступные команды:\n"
        "/start - Подписаться на уведомления\n"
        "/stop - Отписаться от уведомлений\n"
        "/top10 - Топ-10 вирусных блогеров сейчас\n"
        "/mega - Мега вирусные ролики (10x+)\n"
        "/stats - Статистика по вирусному контенту"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stop"""
    user_id = update.effective_user.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        await update.message.reply_text("❌ Вы отписаны от уведомлений")
    else:
        await update.message.reply_text("Вы не были подписаны на уведомления")

async def top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает топ-10 вирусных блогеров"""
    data = load_viral_data()

    if not data:
        await update.message.reply_text("Данные не найдены")
        return

    message = "🔥 ТОП-10 ВИРУСНЫХ БЛОГЕРОВ\n\n"
    for i, blogger in enumerate(data[:10], 1):
        emoji = "🚀" if blogger['viral_coef'] >= 10 else "🔥"
        message += (
            f"{i}. {blogger['name']} ({blogger['platform']})\n"
            f"   {emoji} {blogger['viral_coef']}x | 👁 {blogger['views']}\n"
            f"   🔗 {blogger['url']}\n\n"
        )

    await update.message.reply_text(message)

async def mega_viral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает мега вирусные ролики (10x+)"""
    data = load_viral_data()
    mega = [b for b in data if b['viral_coef'] >= 10]

    if not mega:
        await update.message.reply_text("Пока нет мега вирусных роликов")
        return

    message = "🚀 МЕГА ВИРУСНЫЕ РОЛИКИ (10x+)\n\n"
    for i, blogger in enumerate(mega[:10], 1):
        message += (
            f"{i}. {blogger['name']} ({blogger['platform']})\n"
            f"   🚀 {blogger['viral_coef']}x | 👁 {blogger['views']}\n"
            f"   {blogger['username']}\n"
            f"   🔗 {blogger['url']}\n\n"
        )

    await update.message.reply_text(message)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику"""
    data = load_viral_data()

    total = len(data)
    mega = len([b for b in data if b['viral_coef'] >= 10])
    high = len([b for b in data if 5 <= b['viral_coef'] < 10])

    platforms = {}
    for b in data:
        platforms[b['platform']] = platforms.get(b['platform'], 0) + 1

    message = (
        "📊 СТАТИСТИКА ВИРУСНОГО КОНТЕНТА\n\n"
        f"Всего вирусных блогеров: {total}\n"
        f"🚀 Мега вирусных (10x+): {mega}\n"
        f"🔥 Вирусных (5-10x): {high}\n\n"
        "По платформам:\n"
    )

    for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
        message += f"  • {platform}: {count}\n"

    message += f"\n⏰ Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    await update.message.reply_text(message)

async def check_viral_updates(context: ContextTypes.DEFAULT_TYPE):
    """Периодически проверяет новые вирусные ролики"""
    data = load_viral_data()

    # Находим новые мега вирусные ролики
    new_mega = [b for b in data if b['viral_coef'] >= 15][:5]

    if new_mega and subscribers:
        message = "🚨 НОВЫЙ МЕГА ВИРУСНЫЙ РОЛИК!\n\n"

        for blogger in new_mega:
            message += (
                f"🚀 {blogger['name']} ({blogger['platform']})\n"
                f"Коэффициент: {blogger['viral_coef']}x\n"
                f"Просмотры: {blogger['views']}\n"
                f"Ссылка: {blogger['url']}\n\n"
            )

        # Отправка уведомлений всем подписчикам
        for user_id in subscribers:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

def main():
    """Запуск бота"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("=" * 60)
        print("ОШИБКА: Токен бота не настроен!")
        print("=" * 60)
        print("\nИнструкции:")
        print("1. Создайте бота через @BotFather в Telegram")
        print("2. Скопируйте токен бота")
        print("3. Создайте файл .env с содержимым:")
        print("   TELEGRAM_BOT_TOKEN=ваш_токен")
        print("4. Или отредактируйте переменную BOT_TOKEN в этом файле")
        print("\n" + "=" * 60)
        return

    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("top10", top10))
    application.add_handler(CommandHandler("mega", mega_viral))
    application.add_handler(CommandHandler("stats", stats))

    # Добавление периодической проверки (каждые 30 минут)
    job_queue = application.job_queue
    job_queue.run_repeating(check_viral_updates, interval=CHECK_INTERVAL, first=10)

    print("=" * 60)
    print("🤖 Telegram бот запущен!")
    print("=" * 60)
    print(f"Проверка вирусного контента каждые {CHECK_INTERVAL // 60} минут")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 60)

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
