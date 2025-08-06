import os
import logging
import asyncio
from urllib.parse import urlparse, parse_qs, unquote, urlunparse

from dotenv import load_dotenv
from telegram import Update
from telegram.error import Conflict
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 📤 Декодирование ссылки из параметра ?u= и очистка от трекеров
def clean_url(input_url: str) -> str | None:
    try:
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
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            cleaned_query,
            parsed.fragment
        ))
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")
        return None

# 🚀 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Отправь мне ссылку из Instagram с параметром `?u=...` или любую ссылку с трекерами, "
        "и я верну чистую ссылку.\n\n"
        "Пример:\nhttps://l.instagram.com/?u=https%3A%2F%2Fexample.com..."
    )

# 📩 Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message
        if not user_message or not user_message.text:
            return

        text = user_message.text
        logger.info(f"Получено сообщение: {text}")

        if any(x in text for x in ["l.instagram.com", "?u=", "?fbclid="]):
            cleaned_url = clean_url(text)
            if cleaned_url:
                response = f"Вот чистая ссылка 🔗:\n{cleaned_url}"
                sent_message = await user_message.reply_text(response, disable_web_page_preview=False)
                
                # Удаляем сообщение пользователя через 0.3 секунды
                await asyncio.sleep(0.3)
                try:
                    await user_message.delete()
                except Exception as e:
                    logger.warning(f"Не удалось удалить сообщение: {e}")
            else:
                await user_message.reply_text("❌ Не удалось обработать ссылку.")
        else:
            await user_message.reply_text("❌ Пожалуйста, отправьте ссылку для очистки.")
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")

# ▶️ Запуск бота с обработкой ошибок
async def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Бот запускается...")
        await application.run_polling(drop_pending_updates=True)
    except Conflict:
        logger.error("Бот уже запущен в другом процессе. Остановка.")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
