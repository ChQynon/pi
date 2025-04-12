from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8050987714:AAGEeXCsCVqXrLQjrypQDMys49UWPgpf0NE')
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET-запросов"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Бот для ухода за растениями работает!".encode('utf-8'))
    
    def do_POST(self):
        """Обработка webhook-запросов от Telegram"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Отправляем быстрый ответ, чтобы Telegram не ждал
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
        
        # Обрабатываем данные от Telegram
        try:
            update = json.loads(post_data.decode('utf-8'))
            process_update(update)
        except Exception as e:
            print(f"Ошибка при обработке обновления: {e}")
            

def process_update(update):
    """Обрабатывает обновление от Telegram"""
    # Проверяем, есть ли сообщение в обновлении
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        
        # Проверяем, есть ли текст в сообщении
        if 'text' in message:
            text = message['text']
            
            # Обрабатываем команды
            if text.startswith('/'):
                process_command(chat_id, text)
            else:
                # Отвечаем на обычное сообщение
                send_message(chat_id, f"Вы написали: {text}\n\nЯ могу помочь с уходом за растениями. Используйте /help для списка команд.")
                
    # Здесь можно добавить обработку других типов обновлений (callback_query и т.д.)


def process_command(chat_id, command):
    """Обрабатывает команды бота"""
    command = command.lower()
    
    if command.startswith('/start'):
        text = """👋 Привет! Я бот для ухода за растениями.

🌱 Я могу помочь вам с:
• Распознаванием растений по фото
• Советами по уходу за растениями
• Информацией о витаминах
• Советами по использованию бытовых отходов для удобрения

Используйте /help для получения списка всех команд."""
        send_message(chat_id, text)
        
    elif command.startswith('/help'):
        text = """🌿 *Доступные команды:*

/start - Начать общение с ботом
/help - Показать список команд
/care [название растения] - Получить советы по уходу за растением

📸 Отправьте фото растения, чтобы я его распознал.

🌱 Пример использования команды care:
/care Монстера"""
        send_message(chat_id, text, parse_mode="Markdown")
        
    elif command.startswith('/care'):
        # Извлекаем название растения из команды
        parts = command.split(' ', 1)
        if len(parts) > 1:
            plant_name = parts[1].strip()
            send_care_tips(chat_id, plant_name)
        else:
            send_message(chat_id, "Пожалуйста, укажите название растения после команды. Например: /care Монстера")
    
    else:
        send_message(chat_id, "Неизвестная команда. Используйте /help для получения списка доступных команд.")


def send_care_tips(chat_id, plant_name):
    """Отправляет советы по уходу за растением"""
    # Здесь должна быть логика получения информации о растении
    # Пока используем простую заглушку
    
    plants = {
        "монстера": {
            "name": "Монстера",
            "watering": "Раз в неделю, давая почве подсохнуть между поливами",
            "light": "Яркий непрямой свет",
            "temperature": "18-27°C",
            "soil": "Рыхлая, питательная почва с хорошим дренажем"
        },
        "фикус": {
            "name": "Фикус",
            "watering": "Раз в 7-10 дней, когда верхний слой почвы подсохнет",
            "light": "Яркий непрямой свет",
            "temperature": "18-24°C",
            "soil": "Легкая, питательная почва с хорошим дренажем"
        },
        "суккулент": {
            "name": "Суккулент",
            "watering": "Раз в 2-3 недели, полностью просушивая почву между поливами",
            "light": "Яркое освещение, прямой солнечный свет",
            "temperature": "18-27°C",
            "soil": "Хорошо дренированная, песчаная почва"
        },
        "хлорофитум": {
            "name": "Хлорофитум",
            "watering": "Раз в 7-10 дней, поддерживая почву слегка влажной",
            "light": "Яркий непрямой свет",
            "temperature": "18-24°C",
            "soil": "Легкая, хорошо дренированная почва"
        }
    }
    
    # Приводим к нижнему регистру для поиска
    plant_name_lower = plant_name.lower()
    
    # Ищем растение в нашей базе
    if plant_name_lower in plants:
        plant = plants[plant_name_lower]
        
        text = f"""🌱 *{plant['name']}*

💧 *Полив:* {plant['watering']}

☀️ *Освещение:* {plant['light']}

🌡️ *Температура:* {plant['temperature']}

🌱 *Почва:* {plant['soil']}

💡 *Совет:* Регулярно осматривайте растение на наличие вредителей и заболеваний."""
        
        send_message(chat_id, text, parse_mode="Markdown")
    else:
        # Если растение не найдено
        send_message(chat_id, f"К сожалению, у меня нет информации о растении '{plant_name}'. Попробуйте другое название или отправьте фото растения для распознавания.")


def send_message(chat_id, text, parse_mode=None):
    """Отправляет сообщение пользователю через Telegram API"""
    url = f"{TELEGRAM_API}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text
    }
    
    if parse_mode:
        data["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return None 