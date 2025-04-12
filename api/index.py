import os
import json
import logging
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook

from config import BOT_TOKEN
import main  # Импортируем основной файл бота

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Получаем диспетчер из main.py
dp = main.dp

# URL для установки вебхука
WEBHOOK_HOST = 'https://pi-chqynon.vercel.app'  # Измените на ваш Vercel домен
WEBHOOK_PATH = '/api/webhook'  # Путь к вебхуку
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Путь к SSL сертификату
WEBHOOK_SSL_CERT = None  # На Vercel это не нужно

# Настройки веб-сервера
WEBAPP_HOST = '0.0.0.0'  # или '127.0.0.1'
WEBAPP_PORT = int(os.getenv('PORT', 8000))


# Обработчик HTTP-запросов для Vercel
class handler(BaseHTTPRequestHandler):
    async def setup_webhook(self):
        # Установка вебхука
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != WEBHOOK_URL:
            await bot.set_webhook(
                url=WEBHOOK_URL
            )
            logging.info(f"Webhook set to {WEBHOOK_URL}")

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Bot webhook is running!".encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            logging.info(f"Received update: {update}")
            
            # Передаем обновление в диспетчер aiogram
            process_update(update)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())
        except Exception as e:
            logging.error(f"Error processing update: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())


async def process_update(update_json):
    """Обрабатывает входящие обновления от Telegram API"""
    update = types.Update(**update_json)
    Bot.set_current(bot)
    Dispatcher.set_current(dp)
    await dp.process_update(update)


async def on_startup(dp):
    """Запускается при старте"""
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Starting webhook with URL: {WEBHOOK_URL}")


async def on_shutdown(dp):
    """Запускается при остановке"""
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.info("Bot stopped")


# Для локального запуска с вебхуком (не для Vercel)
if __name__ == '__main__':
    from aiogram import executor
    
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    ) 