import os
import telebot
import sqlite3
import datetime
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем данные из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8362776194:AAFF_1oxvZi2zaNFK8Uy9jKM8dpz3L4Y4Ic')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '-1003253421930'))

bot = telebot.TeleBot(BOT_TOKEN)

def init_database():
    """Инициализация базы данных"""
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

@bot.message_handler(commands=['start', 'status'])
def send_welcome(message):
    """Обработчик команды /start"""
    if message.chat.type != "private":
        return
        
    welcome_text = """
🤗 Добро пожаловать!

Отправьте ваш отзыв о нашей работе.
Можно отправлять текст, фото, видео и другие медиа.
"""
    bot.reply_to(message, welcome_text)
    logger.info(f"Приветствие отправлено {message.from_user.first_name}")

@bot.message_handler(content_types=['text'], func=lambda message: message.chat.type == "private")
def handle_text(message):
    user = message.from_user
    text = message.text
    
    logger.info(f"📝 Текст от {user.first_name}")
    
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
        logger.info("✅ Текст переслан")
    except Exception as e:
        logger.error(f"❌ Ошибка пересылки: {e}")
        bot.send_message(ADMIN_CHAT_ID, f"📝 Текст от {user.first_name}:\n{text}")
    
    bot.reply_to(message, "✅ Спасибо за отзыв!")

@bot.message_handler(content_types=['photo', 'video', 'document'], func=lambda message: message.chat.type == "private")
def handle_media(message):
    user = message.from_user
    caption = message.caption or "Без описания"
    media_type = message.content_type
    
    logger.info(f"📦 {media_type} от {user.first_name}")
    
    # Сохраняем в базу
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (user_id, username, review_text, media_type, date) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.username, caption, media_type, datetime.datetime.now())
    )
    conn.commit()
    conn.close()
    
    # Пересылаем медиа
    try:
        bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
        logger.info(f"✅ {media_type} переслан")
        bot.reply_to(message, f"✅ Спасибо! Ваш {media_type} получен!")
    except Exception as e:
        logger.error(f"❌ Ошибка пересылки {media_type}: {e}")
        bot.send_message(ADMIN_CHAT_ID, f"📦 {media_type} от {user.first_name}\n📝 Описание: {caption}")
        bot.reply_to(message, f"✅ Спасибо! Ваш {media_type} получен!")

if __name__ == "__main__":
    print("🚀 Запуск бота на Render.com...")
    init_database()
    print("🤖 Бот запущен и работает!")
    
    # Бесконечный цикл с перезапуском при ошибках
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"🔄 Перезапуск из-за ошибки: {e}")
            time.sleep(10)
