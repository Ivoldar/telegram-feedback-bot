import os
import telebot
import sqlite3
import datetime
import logging
import time
import threading
from flask import Flask

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем данные из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8362776194:AAFF_1oxvZi2zaNFK8Uy9jKM8dpz3L4Y4Ic')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '-1003253421930'))

bot = telebot.TeleBot(BOT_TOKEN)

# Создаем Flask app для веб-сервера
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is running!"

@app.route('/health')
def health():
    return "OK"

def init_database():
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            review_text TEXT,
            media_type TEXT,
            date TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":
        return

    welcome_text = """
🤗 Добро пожаловать!

Здесь вы можете оставить отзыв о нашей работе.
Ваше мнение очень важно для нас!

Можно отправлять текст, фото, видео и другие медиа.
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text'], func=lambda message: message.chat.type == "private")
def handle_text(message):
    user = message.from_user
    text = message.text

    print(f"📝 Текст от {user.first_name}")

    # Сохраняем в базу
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (user_id, username, review_text, media_type, date) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.username, text, 'text', datetime.datetime.now())
    )
    conn.commit()
    conn.close()

    # Пересылаем
    try:
        bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
        print("✅ Текст переслан")
    except Exception as e:
        print(f"❌ Ошибка пересылки: {e}")
        bot.send_message(ADMIN_CHAT_ID, f"📝 Текст от {user.first_name}:\n{text}")

    bot.reply_to(message, "✅ Спасибо за отзыв!")

@bot.message_handler(content_types=['photo', 'video'], func=lambda message: message.chat.type == "private")
def handle_media(message):
    user = message.from_user
    caption = message.caption or "Без описания"
    media_type = "фото" if message.content_type == 'photo' else "видео"

    print(f"📦 {media_type} от {user.first_name}")

    # Сохраняем в базу
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (user_id, username, review_text, media_type, date) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.username, caption, media_type, datetime.datetime.now())
    )
    conn.commit()
    conn.close()

    # Пересылаем
    try:
        bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
        print(f"✅ {media_type} переслано")
    except Exception as e:
        print(f"❌ Ошибка пересылки {media_type}: {e}")
        bot.send_message(ADMIN_CHAT_ID, f"📦 {media_type} от {user.first_name}\n📝 Описание: {caption}")

    bot.reply_to(message, f"✅ Спасибо! Ваше {media_type} получено!")

def run_bot():
    """Запускает бота в отдельном потоке"""
    print("🤖 Запуск Telegram бота...")
    init_database()
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"🔄 Перезапуск бота из-за ошибки: {e}")
            time.sleep(10)

def run_web_server():
    """Запускает веб-сервер"""
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Запуск веб-сервера на порту {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    print("🚀 Запуск приложения...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-сервер в основном потоке
    run_web_server()
