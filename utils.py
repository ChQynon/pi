def format_vitamin_info(vitamin, detailed=False):
    """Format vitamin information for display"""
    if not vitamin:
        return "Информация не найдена"
    
    if not detailed:
        return f"*{vitamin['name']}*: {vitamin['short_description']}"
    
    text = f"*{vitamin['name']}*\n\n"
    text += f"{vitamin['description']}\n\n"
    
    if 'benefits' in vitamin and vitamin['benefits']:
        text += "*Польза для организма:*\n"
        for benefit in vitamin['benefits'].split('\n'):
            if benefit.strip():
                text += f"• {benefit.strip()}\n"
        text += "\n"
    
    if 'sources' in vitamin and vitamin['sources']:
        text += "*Источники в продуктах:*\n"
        for source in vitamin['sources'].split('\n'):
            if source.strip():
                text += f"• {source.strip()}\n"
        text += "\n"
    
    if 'deficiency' in vitamin and vitamin['deficiency']:
        text += "*При дефиците:*\n"
        for symptom in vitamin['deficiency'].split('\n'):
            if symptom.strip():
                text += f"• {symptom.strip()}\n"
        text += "\n"
    
    if 'overdose' in vitamin and vitamin['overdose']:
        text += "*При избытке:*\n"
        for symptom in vitamin['overdose'].split('\n'):
            if symptom.strip():
                text += f"• {symptom.strip()}\n"
        text += "\n"
    
    if 'daily_intake' in vitamin and vitamin['daily_intake']:
        text += f"*Суточная норма:* {vitamin['daily_intake']}\n\n"
    
    return text


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