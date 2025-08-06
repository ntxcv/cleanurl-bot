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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        
        # Очищаем URL от трекеров
        parsed = urlparse(input_url)
        query_params = parse_qs(parsed.query)
        
        trackers = ['fbclid', 'utm_source', 'utm_medium', 'utm_campaign', 
                   'utm_term', 'utm_content', 'gclid', 'yclid', '_openstat']
        
        for tracker in trackers:
            query_params.pop(tracker, None)
        
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
        logger.error(f"URL processing error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Отправьте мне ссылку для очистки от трекеров.\n"
        "Пример:\nhttps://l.instagram.com/?u=..."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text
        logger.info(f"Received: {text}")

        if any(x in text for x in ["l.instagram.com", "?u=", "?fbclid="]):
            cleaned_url = clean_url(text)
            if cleaned_url:
                await update.message.reply_text(
                    f"🔗 Очищенная ссылка:\n{cleaned_url}",
                    disable_web_page_preview=False
                )
                await asyncio.sleep(0.3)
                try:
                    await update.message.delete()
                except Exception as e:
                    logger.warning(f"Delete failed: {e}")
            else:
                await update.message.reply_text("❌ Не удалось обработать ссылку")
        else:
            await update.message.reply_text("❌ Отправьте ссылку для очистки")
    except Exception as e:
        logger.error(f"Message handling error: {e}")

def main():
    try:
        # Создаем новый event loop для Render
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Starting bot...")
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False  # Важно для Render
        )
    except Conflict:
        logger.error("Bot is already running elsewhere")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped")

if __name__ == '__main__':
    main()
