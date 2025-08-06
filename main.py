import os
import logging
import asyncio
from urllib.parse import urlparse, parse_qs, unquote

from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv(BOT_TOKEN)

# Логгирование
logging.basicConfig(level=logging.INFO)

# 📤 Декодирование ссылки из параметра u=
def extract_and_decode_url(input_url str) - str  None
    parsed = urlparse(input_url)
    query = parse_qs(parsed.query)
    encoded_url = query.get('u', [None])[0]
    return unquote(encoded_url) if encoded_url else None

# 🚀 Команда start
async def start(update Update, context ContextTypes.DEFAULT_TYPE)
    await update.message.reply_text(
        👋 Отправь мне ссылку из сети на букву I с параметром `u=...`, и я верну чистую ссылку.nn
        Примерnhttpsl.isocialnayaset.comu=https%3A%2F%2Fexample.com...
    )

# 📩 Обработка входящих сообщений
async def handle_message(update Update, context ContextTypes.DEFAULT_TYPE)
    user_message Message = update.message
    chat_id = user_message.chat_id
    message_id = user_message.message_id
    text = user_message.text

    # Проверка и обработка ссылки
    if l.instagram.com in text and u= in text
        decoded_url = extract_and_decode_url(text)
        if decoded_url
            # 📤 Отправляем форматированный ответ с превью
            response = fВот чистая ссылка 🔗n{decoded_url}
            await user_message.chat.send_message(response, disable_web_page_preview=False)

            # 🧹 Удаляем сообщение пользователя через 5 секунд
            await asyncio.sleep(0.3)
            try
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e
                logging.warning(fНе удалось удалить сообщение пользователя {e})
        else
            await user_message.reply_text(❌ Не удалось декодировать ссылку.)
    else
        await user_message.reply_text(❌ Пожалуйста, отправь ссылку видаnhttpsl.isocialnayaset.comu=...)

# ▶️ Запуск бота
if __name__ == '__main__'
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler(start, start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(Бот запущен...)
    app.run_polling()
