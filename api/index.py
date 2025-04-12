import os
import json
import logging
from http.server import BaseHTTPRequestHandler
import sys

# Добавляем корень проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


# Обработчик для Vercel serverless функции
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET-запросов"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Бот для ухода за растениями работает!".encode('utf-8'))
    
    def do_POST(self):
        """Обработка webhook-запросов от Telegram"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        logging.info(f"Получен POST запрос на {self.path}")
        
        if self.path == '/api/webhook':
            try:
                update_data = json.loads(post_data.decode('utf-8'))
                logging.info(f"Получено обновление: {update_data}")
                
                # Обработка обновления через aiogram
                from main import process_telegram_update
                process_telegram_update(update_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
                return
            except Exception as e:
                logging.error(f"Ошибка обработки обновления: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode('utf-8'))
                return
        
        # Для всех остальных путей
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": False, "error": "Not found"}).encode('utf-8'))


# Вспомогательная функция для обработки Telegram обновлений
async def process_update(update_data):
    """Обрабатывает входящие обновления от Telegram"""
    update = types.Update(**update_data)
    
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