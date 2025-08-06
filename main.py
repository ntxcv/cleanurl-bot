import os
import logging
import asyncio
from urllib.parse import urlparse, parse_qs, unquote, urlunparse

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Логгирование
logging.basicConfig(level=logging.INFO)

# 📤 Декодирование ссылки из параметра ?u= и очистка от трекеров
def clean_url(input_url: str) -> str | None:
    # Извлекаем URL из параметра u= если это ссылка l.instagram.com
    if "l.instagram.com" in input_url and "?u=" in input_url:
        parsed = urlparse(input_url)
        query = parse_qs(parsed.query)
        encoded_url = query.get('u', [None])[0]
        if not encoded_url:
            return None
        input_url = unquote(encoded_url)
    
    # Очищаем URL от параметров-трекеров
    parsed = urlparse(input_url)
    query_params = parse_qs(parsed.query)
    
    # Список параметров, которые нужно удалить
    trackers = ['fbclid', 'utm_source', 'utm_medium', 'utm_campaign', 
                'utm_term', 'utm_content', 'gclid', 'yclid', '_openstat']
    
    # Удаляем параметры-трекеры
    for tracker in trackers:
        query_params.pop(tracker, None)
    
    # Собираем URL обратно
    cleaned_query = '&'.join(
        f"{k}={v[0]}" for k, v in query_params.items()
    ) if query_params else ''
    
    cleaned_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        cleaned_query,
        parsed.fragment
    ))
    
    return cleaned_url

# 🚀 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Отправь мне ссылку из сети на букву I с параметром `?u=...`, и я верну чистую ссылку.\n\n"
        "Пример:\nhttps://l.instagram.com/?u=https%3A%2F%2Fexample.com..."
    )

# 📩 Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message
    chat_id = user_message.chat_id
    message_id = user_message.message_id
    text = user_message.text

    if text and ("l.instagram.com" in text or "?u=" in text or "?fbclid=" in text):
        cleaned_url = clean_url(text)
        if cleaned_url:
            # 📤 Отправляем форматированный ответ с превью
            response = f"Вот чистая ссылка 🔗:\n{cleaned_url}"
            await user_message.chat.send_message(response, disable_web_page_preview=False)

            # 🧹 Удаляем сообщение пользователя через 0.3 секунды
            await asyncio.sleep(0.3)
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logging.warning(f"Не удалось удалить сообщение пользователя: {e}")
        else:
            await user_message.reply_text("❌ Не удалось обработать ссылку.")
    else:
        await user_message.reply_text("❌ Пожалуйста, отправь ссылку вида:\nhttps://l.instagram.com/?u=...")

# ▶️ Запуск бота
if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    application.run_polling()
