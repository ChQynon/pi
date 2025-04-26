import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN
import bot

# Настройки веб-сервера
WEBHOOK_HOST = os.environ.get('VERCEL_URL', 'your-app.vercel.app')  # URL Vercel приложения
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем экземпляр бота и диспетчера
storage = MemoryStorage()
bot_instance = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=storage)

# Регистрируем роутер
dp.include_router(bot.router)

# Функция для настройки вебхука
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook установлен на {WEBHOOK_URL}")
    await bot.on_startup(bot)

# Функция для удаления вебхука
async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logger.info("Webhook удален")
    await bot.on_shutdown(bot)

# Создаем веб-приложение
app = web.Application()

# Настраиваем вебхук
webhook_request_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot_instance,
)
webhook_request_handler.register(app, path=WEBHOOK_PATH)

# Добавляем обработчики запуска и остановки
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

# Настраиваем роуты
setup_application(app, dp, bot=bot_instance)

# Эта функция создает приложение для Vercel
def create_app():
    return app

# Для локального тестирования
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080) 