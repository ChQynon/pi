import os
import re
import time
import random
import logging
import aiohttp
import asyncio
import datetime
import traceback
from typing import Dict, List, Union, Optional, Any

from config import TEMP_DIR, MEDIA_DIR

logger = logging.getLogger(__name__)

async def download_image(url: str, save_path: str = None) -> Optional[str]:
    try:
        if not save_path:
            os.makedirs(TEMP_DIR, exist_ok=True)
            filename = f"temp_image_{int(time.time())}_{random.randint(1000, 9999)}.jpg"
            save_path = os.path.join(TEMP_DIR, filename)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download image: {response.status}")
                    return None
                
                with open(save_path, 'wb') as f:
                    f.write(await response.read())
                
                logger.info(f"Image downloaded to {save_path}")
                return save_path
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None

async def fetch_url(url: str) -> Optional[Dict]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch URL: {response.status}")
                    return None
                
                return await response.json()
    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        return None

def format_plant_info(plant_data: Dict) -> str:
    if not plant_data:
        return "Информация о растении не найдена."
    
    info = f"🌱 <b>{plant_data.get('name', 'Неизвестное растение')}</b>\n"
    
    if plant_data.get('scientific_name'):
        info += f"<i>{plant_data['scientific_name']}</i>\n\n"
    else:
        info += "\n"
    
    if plant_data.get('description'):
        info += f"{plant_data['description']}\n\n"
    
    if plant_data.get('type'):
        info += f"<b>Тип:</b> {plant_data['type']}\n"
    
    care_tips = plant_data.get('care_tips', {})
    if isinstance(care_tips, dict) and care_tips:
        info += "\n<b>Рекомендации по уходу:</b>\n"
        for key, value in care_tips.items():
            if key == 'general':
                info += f"{value}\n"
            elif value:
                info += f"• <b>{key.capitalize()}:</b> {value}\n"
    elif isinstance(care_tips, str) and care_tips:
        info += f"\n<b>Рекомендации по уходу:</b>\n{care_tips}\n"
    
    common_problems = plant_data.get('common_problems', [])
    if common_problems:
        info += "\n<b>Распространенные проблемы:</b>\n"
        if isinstance(common_problems, list):
            for problem in common_problems:
                if problem:
                    info += f"• {problem}\n"
        else:
            info += f"{common_problems}\n"
    
    if plant_data.get('benefits'):
        info += f"\n<b>Польза:</b>\n{plant_data['benefits']}\n"
    
    return info

def format_vitamin_info(vitamin_data: Dict) -> str:
    if not vitamin_data:
        return "Информация о витамине не найдена."
    
    info = f"💊 <b>{vitamin_data.get('name', 'Неизвестный витамин')}</b>\n\n"
    
    if vitamin_data.get('description'):
        info += f"{vitamin_data['description']}\n\n"
    
    if vitamin_data.get('benefits'):
        benefits = vitamin_data['benefits'].replace('\n', '\n• ')
        info += f"<b>Польза:</b>\n• {benefits}\n\n"
    
    if vitamin_data.get('sources'):
        sources = vitamin_data['sources'].replace('\n', '\n• ')
        info += f"<b>Натуральные источники:</b>\n• {sources}\n\n"
    
    if vitamin_data.get('deficiency'):
        deficiency = vitamin_data['deficiency'].replace('\n', '\n• ')
        info += f"<b>Признаки дефицита:</b>\n• {deficiency}\n\n"
    
    if vitamin_data.get('daily_intake'):
        info += f"<b>Рекомендуемая дневная доза:</b> {vitamin_data['daily_intake']}\n\n"
    
    if vitamin_data.get('overdose'):
        overdose = vitamin_data['overdose'].replace('\n', '\n• ')
        info += f"<b>Признаки передозировки:</b>\n• {overdose}\n"
    
    info += "\n<i>⚠️ Прежде чем принимать витаминные добавки, проконсультируйтесь с врачом.</i>"
    
    return info

def extract_entities(text: str) -> Dict[str, List[str]]:
    entities = {
        'vitamins': [],
        'plants': [],
        'minerals': [],
        'nutrients': []
    }
    
    vitamin_pattern = r'витамин[а-я]* [ABCDEK]\d*'
    plant_pattern = r'(алоэ|каланхоэ|фикус|кактус|суккулент|орхидея|фиалка|бегония|монстера|хлорофитум)'
    mineral_pattern = r'(кальций|магний|цинк|железо|селен|йод|калий)'
    nutrient_pattern = r'(белок|углевод|жир|клетчатка|антиоксидант)'
    
    vitamins = re.findall(vitamin_pattern, text.lower())
    plants = re.findall(plant_pattern, text.lower())
    minerals = re.findall(mineral_pattern, text.lower())
    nutrients = re.findall(nutrient_pattern, text.lower())
    
    entities['vitamins'] = list(set(vitamins))
    entities['plants'] = list(set(plants))
    entities['minerals'] = list(set(minerals))
    entities['nutrients'] = list(set(nutrients))
    
    return entities

def clean_text(text: str) -> str:
    return re.sub(r'[^\w\s\.\,\-\?\!]', '', text)

def log_user_action(user_id, username, action, details=None):
    try:
        logger.info(f"USER ACTION: {user_id} (@{username}) - {action} - {details or ''}")
    except Exception as e:
        logger.error(f"Error logging user action: {e}")

async def rate_limit(user_state, key, rate_limit_seconds=5):
    current_time = time.time()
    last_time = user_state.get(f"last_{key}_time", 0)
    
    if current_time - last_time < rate_limit_seconds:
        return False
    
    user_state[f"last_{key}_time"] = current_time
    return True

def format_ai_response(response: str) -> str:
    response = response.replace('**', '<b>').replace('__', '<i>')
    response = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', response)
    response = re.sub(r'__(.+?)__', r'<i>\1</i>', response)
    
    response = re.sub(r'\n\n+', '\n\n', response)
    
    section_pattern = r'\*\*([^:]+):\*\*'
    sections = re.findall(section_pattern, response)
    
    for section in sections:
        original = f"**{section}:**"
        replacement = f"<b>{section}:</b>"
        response = response.replace(original, replacement)
    
    return response

def format_plant_tip(plant_tip, detailed=False):
    """Format plant care tip for display"""
    if not plant_tip:
        return "Информация не найдена"
    
    if not detailed:
        return f"*{plant_tip['waste_type']}*: {plant_tip['short_description']}"
    
    text = f"*{plant_tip['waste_type']}*\n\n"
    text += f"{plant_tip['description']}\n\n"
    
    if 'benefits' in plant_tip and plant_tip['benefits']:
        text += "*Польза для растений:*\n"
        for benefit in plant_tip['benefits'].split('\n'):
            if benefit.strip():
                text += f"• {benefit.strip()}\n"
        text += "\n"
    
    if 'application' in plant_tip and plant_tip['application']:
        text += "*Способ применения:*\n"
        for step in plant_tip['application'].split('\n'):
            if step.strip():
                text += f"• {step.strip()}\n"
        text += "\n"
    
    if 'suitable_plants' in plant_tip and plant_tip['suitable_plants']:
        text += "*Подходит для растений:*\n"
        for plant in plant_tip['suitable_plants'].split('\n'):
            if plant.strip():
                text += f"• {plant.strip()}\n"
        text += "\n"
    
    if 'precautions' in plant_tip and plant_tip['precautions']:
        text += "*Предостережения:*\n"
        for precaution in plant_tip['precautions'].split('\n'):
            if precaution.strip():
                text += f"• {precaution.strip()}\n"
        text += "\n"
    
    return text

def format_faq(faq_id):
    """Return formatted FAQ text based on ID"""
    faqs = {
        "about": {
            "title": "О боте",
            "text": (
                "Этот бот создан для предоставления информации о витаминах, минералах и правильном использовании "
                "бытовых отходов для ухода за комнатными растениями.\n\n"
                "Функции бота:\n"
                "• Информация о витаминах и минералах\n"
                "• Советы по уходу за растениями\n"
                "• AI консультации по индивидуальным вопросам\n"
                "• Анализ фотографий растений\n"
                "• Решение проблем с витаминами и растениями\n\n"
                "Бот постоянно обновляется новой информацией и возможностями."
            )
        },
        "how_to_search": {
            "title": "Как искать информацию",
            "text": (
                "Существует несколько способов найти нужную информацию:\n\n"
                "1. Выберите соответствующий раздел в меню (Витамины, Растения и т.д.)\n\n"
                "2. Напишите ваш вопрос в чат, например:\n"
                "   • 'Витамин D'\n"
                "   • 'Как использовать яичную скорлупу для растений'\n\n"
                "3. Используйте AI Консультанта для сложных вопросов\n\n"
                "4. В разделе 'Проблемы и решения' опишите свою конкретную проблему\n\n"
                "Помните, что можно всегда вернуться в главное меню, нажав соответствующую кнопку."
            )
        },
        "sources": {
            "title": "Источники информации",
            "text": (
                "Информация в этом боте основана на авторитетных научных и образовательных источниках:\n\n"
                "• Медицинские справочники и базы данных о витаминах и минералах\n\n"
                "• Научные публикации по агрономии и уходу за растениями\n\n"
                "• Рекомендации профессиональных садоводов и биологов\n\n"
                "• AI алгоритмы, обученные на обширных научных данных\n\n"
                "Вся информация регулярно обновляется для соответствия актуальным исследованиям."
            )
        },
        "ai_features": {
            "title": "Об AI возможностях",
            "text": (
                "Бот использует современные AI технологии для предоставления персонализированных ответов:\n\n"
                "1. *Общие вопросы* - задавайте вопросы на любые темы, связанные с витаминами и растениями\n\n"
                "2. *Рекомендация витаминов* - получите персональные рекомендации по приему витаминов\n\n"
                "3. *Анализ растения* - отправьте фото вашего растения для идентификации и советов по уходу\n\n"
                "4. *Решение проблем* - опишите проблему, и AI поможет найти решение\n\n"
                "5. *Актуальная информация* - запросите последние научные данные по интересующей теме"
            )
        },
        "problem_solving": {
            "title": "О решении проблем",
            "text": (
                "Бот поможет решить типичные проблемы с витаминами и растениями:\n\n"
                "1. Выберите раздел *Проблемы и решения* в главном меню\n\n"
                "2. Выберите категорию проблемы или опишите ее своими словами\n\n"
                "3. Бот проанализирует проблему, предложит причины и решения\n\n"
                "Для более точных результатов старайтесь максимально подробно описать проблему."
            )
        }
    }
    
    if faq_id not in faqs:
        return None
    
    faq = faqs[faq_id]
    return f"*{faq['title']}*\n\n{faq['text']}"

def is_vitamin_query(text):
    """Check if text likely contains a vitamin query"""
    text = text.lower()
    vitamin_keywords = ['витамин', 'минерал', 'кальций', 'железо', 'магний', 
                        'цинк', 'калий', 'натрий', 'фосфор', 'йод', 'селен']
    return any(keyword in text for keyword in vitamin_keywords)

def is_plant_query(text):
    """Check if text likely contains a plant care query"""
    text = text.lower()
    plant_keywords = ['растение', 'цветок', 'уход', 'полив', 'удобрение', 'почва',
                     'скорлупа', 'кожура', 'гуща', 'заварка', 'компост']
    return any(keyword in text for keyword in plant_keywords)

def get_file_url(file_path, bot_token):
    """Get full file URL from file path"""
    return f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

def is_health_query(text):
    """Check if text likely contains a health query"""
    text = text.lower()
    health_keywords = ['здоровье', 'самочувствие', 'сон', 'усталость', 'болезнь', 
                      'симптом', 'лечение', 'профилактика', 'иммунитет']
    return any(keyword in text for keyword in health_keywords)

def is_ai_query(text):
    """Check if text likely contains an AI query"""
    text = text.lower()
    ai_keywords = ['ai', 'искусственный интеллект', 'анализ', 'помоги', 'посоветуй', 
                  'что делать', 'как быть', 'объясни', 'расскажи', 'консультант']
    return any(keyword in text for keyword in ai_keywords)

def format_problem_analysis(analysis, problem_type):
    """Format problem analysis for display"""
    # For simple responses, just return the analysis as is
    if not analysis.startswith("**"):
        return analysis
    
    # For structured responses, add a header based on problem type
    if problem_type == "vitamin":
        header = "🔍 *Анализ проблемы с витаминами*\n\n"
    elif problem_type == "plant":
        header = "🔍 *Анализ проблемы с растением*\n\n"
    else:
        header = "🔍 *Анализ проблемы*\n\n"
    
    # Replace markdown formatting for Telegram
    formatted_analysis = analysis.replace("**", "*")
    
    return header + formatted_analysis

def clean_markdown(text):
    """Clean markdown formatting from text while preserving Telegram markdown
    
    Args:
        text (str): Text with potentially incorrect markdown
        
    Returns:
        str: Cleaned text with proper Telegram markdown
    """
    if not text:
        return text
        
    # Remove or replace problematic markdown
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("**", "*")  # Convert bold to Telegram format
    
    # Ensure there are even number of asterisks for proper Telegram formatting
    asterisk_count = text.count("*")
    if asterisk_count % 2 != 0:
        # Find the last asterisk and remove it if unmatched
        last_pos = text.rfind("*")
        if last_pos >= 0:
            text = text[:last_pos] + text[last_pos+1:]
            
    return text 