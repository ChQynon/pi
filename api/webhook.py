from flask import Flask, request, jsonify
import logging
import json
import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN
import main

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = main.dp  # Используем диспетчер из main.py

# URL для вебхука
WEBHOOK_HOST = os.environ.get('VERCEL_URL', 'https://pi-chqynon.vercel.app')
WEBHOOK_PATH = '/api/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


@app.route('/api/webhook', methods=['POST'])
async def webhook():
    """Обработчик вебхука от Telegram"""
    if request.method == 'POST':
        try:
            update_json = request.get_json()
            logger.info(f"Received update: {update_json}")
            
            # Преобразуем JSON в объект Update
            update = types.Update(**update_json)
            
            # Устанавливаем текущий бот и диспетчер
            Bot.set_current(bot)
            Dispatcher.set_current(dp)
            
            # Обрабатываем обновление
            await dp.process_update(update)
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Method not allowed"}), 405


@app.route('/', methods=['GET'])
def index():
    """Корневой маршрут для проверки работоспособности"""
    return "Telegram Bot Webhook is running!"


@app.route('/api/set_webhook', methods=['GET'])
async def set_webhook():
    """Установка вебхука"""
    try:
        webhook_info = await bot.get_webhook_info()
        
        if webhook_info.url != WEBHOOK_URL:
            await bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"Webhook set to {WEBHOOK_URL}")
            return jsonify({"status": "ok", "message": f"Webhook set to {WEBHOOK_URL}"})
        else:
            return jsonify({"status": "ok", "message": "Webhook already set"})
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Локальный запуск для тестирования
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000))) 