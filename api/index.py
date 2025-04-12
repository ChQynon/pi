from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import base64
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8050987714:AAGEeXCsCVqXrLQjrypQDMys49UWPgpf0NE')
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHUTES_API_TOKEN = os.environ.get('CHUTES_API_TOKEN', 'cpk_7e4ce4743c7545fa8217818d9ca46e55.e1a9c74707105d49ba223a1dc3616256.YSAyEpMPrvBy93xL8IBLo7u1zbSnMWKS')

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
            logger.error(f"Ошибка при обработке обновления: {e}")
            

def process_update(update):
    """Обрабатывает обновление от Telegram"""
    try:
        # Обработка сообщений
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            username = message['from'].get('username', '')
            first_name = message['from'].get('first_name', '')
            
            # Регистрируем пользователя (для аналитики)
            register_user(user_id, username, first_name)
            
            # Обработка фото
            if 'photo' in message:
                # Если пользователь отправил фото
                photos = message['photo']
                # Берем фото с самым высоким разрешением
                photo = photos[-1]
                file_id = photo['file_id']
                
                # Обрабатываем фото растения
                process_plant_photo(chat_id, file_id)
                return
            
            # Обработка текста
            if 'text' in message:
                text = message['text']
                
                # Обрабатываем команды
                if text.startswith('/'):
                    process_command(chat_id, text, user_id)
                else:
                    # Анализируем запрос через ИИ
                    process_text_query(chat_id, text, user_id)
        
        # Обработка обратных вызовов от кнопок
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            chat_id = callback_query['message']['chat']['id']
            user_id = callback_query['from']['id']
            callback_data = callback_query['data']
            message_id = callback_query['message']['message_id']
            
            # Отправляем уведомление, что получили callback
            answer_callback_query(callback_query['id'])
            
            # Обрабатываем callback в зависимости от данных
            if callback_data.startswith('new_plant_care'):
                # Спрашиваем название растения
                ask_plant_name(chat_id)
            elif callback_data.startswith('vit_'):
                # Показываем информацию о витамине
                vitamin_name = callback_data[4:]
                show_vitamin_info(chat_id, vitamin_name)
            else:
                # Обработка других типов callback
                send_message(chat_id, f"Получен callback: {callback_data}")
                
    except Exception as e:
        logger.error(f"Ошибка в process_update: {e}")


def process_command(chat_id, command, user_id=None):
    """Обрабатывает команды бота"""
    command = command.lower()
    
    if command.startswith('/start'):
        send_welcome_message(chat_id)
        
    elif command.startswith('/help'):
        send_help_message(chat_id)
        
    elif command.startswith('/care'):
        # Извлекаем название растения из команды
        parts = command.split(' ', 1)
        if len(parts) > 1:
            plant_name = parts[1].strip()
            send_care_tips(chat_id, plant_name)
        else:
            send_message(chat_id, "Пожалуйста, укажите название растения после команды. Например: /care Монстера")
    
    elif command.startswith('/vitamins'):
        send_vitamins_list(chat_id)
        
    elif command.startswith('/feedback'):
        ask_for_feedback(chat_id)
        
    else:
        send_message(chat_id, "Неизвестная команда. Используйте /help для получения списка доступных команд.")


def send_welcome_message(chat_id):
    """Отправляет приветственное сообщение"""
    text = """👋 Привет! Я бот для ухода за растениями и информации о витаминах.

🌱 Я могу помочь вам с:
• Распознаванием растений по фото
• Советами по уходу за растениями
• Информацией о витаминах
• Советами по использованию бытовых отходов для удобрения

Выберите раздел, который вас интересует:"""
    
    # Создаем клавиатуру
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🌿 Распознать растение", "callback_data": "recognize_plant"}
            ],
            [
                {"text": "💧 Советы по уходу", "callback_data": "care_tips"}
            ],
            [
                {"text": "💊 Информация о витаминах", "callback_data": "vitamins_info"}
            ],
            [
                {"text": "♻️ Органические удобрения", "callback_data": "organic_fertilizers"}
            ]
        ]
    }
    
    send_message(chat_id, text, reply_markup=keyboard)


def send_help_message(chat_id):
    """Отправляет сообщение с помощью"""
    text = """🌿 *Доступные команды:*

/start - Начать общение с ботом
/help - Показать список команд
/care [название растения] - Получить советы по уходу за растением
/vitamins - Список витаминов

📸 Отправьте фото растения, чтобы я его распознал.

🌱 Пример использования команды care:
/care Монстера"""
    
    send_message(chat_id, text, parse_mode="Markdown")


def process_plant_photo(chat_id, file_id):
    """Обрабатывает фото растения"""
    try:
        # Получаем URL файла
        file_info = get_file_info(file_id)
        if not file_info or 'file_path' not in file_info:
            send_message(chat_id, "Не удалось получить информацию о фото. Пожалуйста, попробуйте еще раз.")
            return
            
        file_path = file_info['file_path']
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        # Отправляем сообщение о том, что фото обрабатывается
        send_message(chat_id, "🔍 Анализирую фото растения... Это может занять несколько секунд.")
        
        # Распознаем растение через ИИ
        recognition_result = recognize_plant_with_ai(file_url)
        
        if not recognition_result.get("recognized", False):
            send_message(chat_id, "😔 Не удалось распознать растение на фото. Пожалуйста, попробуйте сделать более четкое фото при хорошем освещении.")
            return
            
        # Отправляем результат распознавания
        plant_name = recognition_result.get("name", "Неизвестное растение")
        description = recognition_result.get("description", "")
        care_tips = recognition_result.get("care_tips", {})
        
        # Формируем текст ответа
        text = f"🌱 *{plant_name}*\n\n"
        
        if description:
            text += f"{description}\n\n"
            
        if care_tips:
            text += "*Рекомендации по уходу:*\n\n"
            
            if "watering" in care_tips:
                text += f"💧 *Полив:* {care_tips['watering']}\n\n"
                
            if "light" in care_tips:
                text += f"☀️ *Освещение:* {care_tips['light']}\n\n"
                
            if "temperature" in care_tips:
                text += f"🌡️ *Температура:* {care_tips['temperature']}\n\n"
                
            if "soil" in care_tips:
                text += f"🌱 *Почва:* {care_tips['soil']}\n\n"
        
        # Добавляем кнопки
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔍 Другое растение", "callback_data": "new_plant_care"},
                    {"text": "👍 Спасибо!", "callback_data": f"thanks_care_{plant_name}"}
                ]
            ]
        }
        
        send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        send_message(chat_id, "Произошла ошибка при обработке фото. Пожалуйста, попробуйте позже.")


def recognize_plant_with_ai(image_url):
    """Распознает растение с помощью ИИ"""
    try:
        # Заглушка для эмуляции работы ИИ
        # В реальном приложении здесь должен быть запрос к API ИИ
        
        # Предположим, что мы всегда распознаем Монстеру
        result = {
            "recognized": True,
            "name": "Монстера",
            "scientific_name": "Monstera deliciosa",
            "description": "Крупное тропическое растение с характерными разрезными листьями, популярное в домашнем озеленении.",
            "care_tips": {
                "watering": "Раз в неделю, давая почве подсохнуть между поливами",
                "light": "Яркий непрямой свет",
                "temperature": "18-27°C",
                "soil": "Рыхлая, питательная почва с хорошим дренажем"
            },
            "common_problems": [
                "Коричневые края листьев",
                "Желтые листья",
                "Отсутствие разрезов на листьях"
            ]
        }
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при распознавании растения: {e}")
        return {"recognized": False, "error": str(e)}


def process_text_query(chat_id, text, user_id=None):
    """Обрабатывает текстовые запросы пользователя через ИИ"""
    try:
        # Проверяем, является ли запрос вопросом о витамине
        if "витамин" in text.lower():
            # Извлекаем название витамина
            vitamin_name = extract_vitamin_name(text)
            if vitamin_name:
                show_vitamin_info(chat_id, vitamin_name)
                return
                
        # Проверяем, является ли запрос вопросом о растении
        plant_name = extract_plant_name(text)
        if plant_name:
            send_care_tips(chat_id, plant_name)
            return
            
        # Если не удалось определить тип запроса, обрабатываем через общий ИИ
        ai_response = generate_ai_response(text)
        send_message(chat_id, ai_response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового запроса: {e}")
        send_message(chat_id, "Извините, произошла ошибка при обработке вашего запроса.")


def extract_vitamin_name(text):
    """Извлекает название витамина из текста"""
    # Простая реализация - ищем "витамин X" в тексте
    text = text.lower()
    vitamins = ["A", "B", "C", "D", "E", "K"]
    
    for vitamin in vitamins:
        if f"витамин {vitamin}" in text:
            return vitamin
            
    return None


def extract_plant_name(text):
    """Извлекает название растения из текста"""
    # Простая реализация - проверяем наличие названий растений в тексте
    plants = ["монстера", "фикус", "суккулент", "хлорофитум"]
    
    for plant in plants:
        if plant in text.lower():
            return plant
            
    return None


def generate_ai_response(text):
    """Генерирует ответ с помощью ИИ"""
    # Заглушка для эмуляции работы ИИ
    return f"Я понял ваш вопрос: \"{text}\"\n\nК сожалению, сейчас я не могу дать подробный ответ. Пожалуйста, используйте команды /care, /vitamins или отправьте фото растения для распознавания."


def send_vitamins_list(chat_id):
    """Отправляет список доступных витаминов"""
    text = """💊 *Доступные витамины:*

Выберите витамин, чтобы узнать больше:"""
    
    # Создаем клавиатуру с кнопками витаминов
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Витамин A", "callback_data": "vit_A"},
                {"text": "Витамин B", "callback_data": "vit_B"},
                {"text": "Витамин C", "callback_data": "vit_C"}
            ],
            [
                {"text": "Витамин D", "callback_data": "vit_D"},
                {"text": "Витамин E", "callback_data": "vit_E"},
                {"text": "Витамин K", "callback_data": "vit_K"}
            ]
        ]
    }
    
    send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)


def show_vitamin_info(chat_id, vitamin_name):
    """Показывает информацию о витамине"""
    # Словарь с информацией о витаминах
    vitamins = {
        "A": {
            "name": "Витамин A",
            "description": "Жирорастворимый витамин, важный для зрения, иммунной системы и роста клеток.",
            "sources": "Морковь, сладкий картофель, шпинат, печень, яичный желток",
            "benefits": "Поддерживает зрение, иммунитет и здоровье кожи",
            "deficiency": "Ухудшение зрения в темноте, сухость кожи, частые инфекции"
        },
        "C": {
            "name": "Витамин C",
            "description": "Мощный антиоксидант, необходимый для роста и восстановления тканей организма.",
            "sources": "Цитрусовые, киви, шиповник, сладкий перец, брокколи",
            "benefits": "Укрепляет иммунитет, ускоряет заживление ран, улучшает усвоение железа",
            "deficiency": "Частые простуды, медленное заживление ран, кровоточивость десен"
        },
        "D": {
            "name": "Витамин D",
            "description": "Жирорастворимый витамин, регулирующий усвоение кальция и фосфора.",
            "sources": "Жирная рыба, яичные желтки, грибы, вырабатывается в коже под воздействием солнечных лучей",
            "benefits": "Укрепляет кости и зубы, поддерживает иммунитет, регулирует настроение",
            "deficiency": "Рахит у детей, остеопороз у взрослых, мышечная слабость, депрессия"
        }
    }
    
    # Если информация о витамине есть в словаре
    if vitamin_name in vitamins:
        vitamin = vitamins[vitamin_name]
        
        text = f"""*{vitamin['name']}*

{vitamin['description']}

*Источники:*
{vitamin['sources']}

*Польза:*
{vitamin['benefits']}

*Признаки дефицита:*
{vitamin['deficiency']}"""
        
        # Кнопка для возврата к списку витаминов
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "← Назад к списку витаминов", "callback_data": "vitamins_list"}
                ]
            ]
        }
        
        send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        # Если информации о витамине нет
        send_message(chat_id, f"К сожалению, у меня нет информации о витамине {vitamin_name}. Используйте /vitamins для просмотра доступных витаминов.")


def ask_plant_name(chat_id):
    """Спрашивает у пользователя название растения"""
    send_message(
        chat_id,
        "Пожалуйста, введите название растения, о котором хотите узнать:",
        reply_markup={"force_reply": True}
    )


def ask_for_feedback(chat_id):
    """Запрашивает отзыв у пользователя"""
    send_message(
        chat_id,
        "Пожалуйста, напишите ваш отзыв о работе бота. Это поможет нам улучшить сервис:",
        reply_markup={"force_reply": True}
    )


def register_user(user_id, username, first_name):
    """Регистрирует пользователя в системе"""
    # В реальном приложении здесь должно быть сохранение в базу данных
    logger.info(f"Зарегистрирован пользователь: {username} (ID: {user_id})")


def send_care_tips(chat_id, plant_name):
    """Отправляет советы по уходу за растением"""
    # Словарь с информацией о растениях
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
    
    # Ищем растение в словаре
    if plant_name_lower in plants:
        plant = plants[plant_name_lower]
        
        text = f"""🌱 *{plant['name']}*

💧 *Полив:* {plant['watering']}

☀️ *Освещение:* {plant['light']}

🌡️ *Температура:* {plant['temperature']}

🌱 *Почва:* {plant['soil']}

💡 *Совет:* Регулярно осматривайте растение на наличие вредителей и заболеваний."""
        
        # Кнопки для дополнительных действий
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔍 Другое растение", "callback_data": "new_plant_care"},
                    {"text": "👍 Спасибо!", "callback_data": f"thanks_care_{plant['name']}"}
                ]
            ]
        }
        
        send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        # Если растение не найдено
        text = f"К сожалению, у меня нет информации о растении '{plant_name}'. Попробуйте другое название или отправьте фото растения для распознавания."
        
        # Кнопка для распознавания по фото
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "📸 Распознать по фото", "callback_data": "recognize_plant"}
                ]
            ]
        }
        
        send_message(chat_id, text, reply_markup=keyboard)


# Вспомогательные функции для работы с Telegram API

def get_file_info(file_id):
    """Получает информацию о файле"""
    url = f"{TELEGRAM_API}/getFile"
    params = {"file_id": file_id}
    
    try:
        response = requests.get(url, params=params)
        result = response.json()
        
        if result.get("ok", False):
            return result["result"]
        else:
            logger.error(f"Ошибка получения информации о файле: {result}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при запросе информации о файле: {e}")
        return None


def answer_callback_query(callback_query_id, text=None):
    """Отвечает на callback query"""
    url = f"{TELEGRAM_API}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    
    if text:
        data["text"] = text
        
    try:
        requests.post(url, json=data)
    except Exception as e:
        logger.error(f"Ошибка при ответе на callback query: {e}")


def send_message(chat_id, text, parse_mode=None, reply_markup=None):
    """Отправляет сообщение пользователю через Telegram API"""
    url = f"{TELEGRAM_API}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text
    }
    
    if parse_mode:
        data["parse_mode"] = parse_mode
        
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return None 