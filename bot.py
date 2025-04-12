import logging
import re
import asyncio
import os
import signal
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)

from config import BOT_TOKEN
from database import Database
from keyboards import (
    get_main_menu_keyboard, 
    get_vitamins_menu_keyboard, 
    get_plants_menu_keyboard,
    get_faq_keyboard,
    get_back_keyboard,
    get_ai_consultant_keyboard,
    get_cancel_keyboard,
    get_problems_menu_keyboard,
    get_ai_menu_keyboard,
    get_plant_actions_keyboard
)
from utils import (
    format_vitamin_info, 
    format_plant_tip, 
    format_faq,
    is_vitamin_query,
    is_plant_query,
    is_health_query,
    is_ai_query,
    get_file_url,
    format_problem_analysis,
    clean_markdown
)
from ai_service import AIService

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
FEEDBACK = 0
WAITING_FOR_GENERAL_QUESTION = 1
WAITING_FOR_VITAMIN_QUERY = 2
WAITING_FOR_PLANT_IMAGE = 3
WAITING_FOR_PROBLEM_DESCRIPTION = 4
WAITING_FOR_KNOWLEDGE_UPDATE_TOPIC = 5

# Initialize database connection
db = Database()

# Initialize AI service
ai_service = AIService()

def escape_markdown(text, version=1):
    """
    Helper function to escape telegram markup symbols.
    
    Args:
        text (str): The text to escape.
        version (int): The version of Telegram's Markdown parser to use
                      (1 for MarkdownV1, 2 for MarkdownV2)
    
    Returns:
        str: The escaped text.
    """
    if version == 1:
        escape_chars = r'_*`['
    else:  # For MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    # Create user in database if doesn't exist
    if user.username:
        username = user.username
    else:
        username = f"{user.first_name} {user.last_name if user.last_name else ''}"
    
    db.register_user(user.id, username, user.first_name)
    
    welcome_message = (
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        f"Я *PLEXY* - информационный бот, созданный *SAMGA_NIS*.\n\n"
        f"Я могу:\n"
        f"🌿 Определять растения по фото\n"
        f"💊 Предоставлять информацию о витаминах и микроэлементах\n"
        f"❓ Отвечать на ваши вопросы с помощью ИИ\n\n"
        f"Выберите интересующую вас категорию или используйте команду /help для получения списка всех команд."
    )
    
    # Track user interaction
    db.update_user_interaction(user.id, "start")
    
    await update.message.reply_markdown_v2(
        escape_markdown(welcome_message, 2),
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "*PLEXY* - Ваш информационный бот от *SAMGA_NIS*\n\n"
        "*Основные команды:*\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/plants - Информация о растениях\n"
        "/vitamins - Информация о витаминах\n"
        "/ai - ИИ-консультант\n"
        "/feedback - Оставить отзыв\n\n"
        
        "*Функции:*\n"
        "🌿 *Распознавание растений:* отправьте фото любого растения, и я определю его вид и предоставлю информацию о нем\n"
        "💊 *Информация о витаминах:* получите подробную информацию о витаминах, микроэлементах и их пользе\n"
        "❓ *ИИ-консультант:* задайте мне любой вопрос, и я постараюсь на него ответить\n\n"
        
        "Чтобы вернуться в главное меню из любого раздела, нажмите соответствующую кнопку в меню."
    )
    
    # Track user interaction
    user_id = update.effective_user.id
    db.update_user_interaction(user_id, "help")
    
    await update.message.reply_markdown_v2(
        escape_markdown(help_text, 2),
        reply_markup=get_main_menu_keyboard()
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for text messages"""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Check if the message is a menu button press
    if text == "🍏 Витамины и минералы":
        return await show_vitamins_menu(update, context)
    elif text == "🌱 Уход за растениями":
        return await show_plants_menu(update, context)
    elif text == "🤖 AI Консультант":
        return await show_ai_menu(update, context)
    elif text == "❓ FAQ":
        return await show_faq(update, context)
    elif text == "📝 Обратная связь":
        return await start_feedback(update, context)
    elif text == "🔍 Проблемы и решения":
        return await show_problems_menu(update, context)
    
    # Check if in conversation state
    if context.user_data.get('state') == WAITING_FOR_GENERAL_QUESTION:
        await handle_ai_general_question(update, context, text)
        return
    elif context.user_data.get('state') == WAITING_FOR_VITAMIN_QUERY:
        await handle_ai_vitamin_recommendation(update, context, text)
        return
    elif context.user_data.get('state') == WAITING_FOR_PROBLEM_DESCRIPTION:
        await handle_problem_description(update, context, text)
        return
    
    # Check if it seems like an AI query
    if is_ai_query(text) or is_health_query(text):
        await handle_ai_general_question(update, context, text)
        return
    
    # Otherwise, process as a regular search query
    if is_vitamin_query(text):
        # Extract possible vitamin name
        vitamin_pattern = r"витамин\s+([a-zA-Zа-яА-Я\d]+)"
        match = re.search(vitamin_pattern, text.lower())
        
        if match:
            vitamin_name = match.group(1)
            vitamin = db.get_vitamin_by_name(f"Витамин {vitamin_name}")
            
            if vitamin:
                await update.message.reply_text(
                    format_vitamin_info(vitamin, detailed=True),
                    parse_mode=ParseMode.MARKDOWN
                )
                db.update_user_interaction(user_id, "vitamins")
                return
        
        # If no exact match, try search
        results = db.search_vitamins(text)
        
        if results:
            if len(results) == 1:
                # If only one result, show detailed info
                await update.message.reply_text(
                    format_vitamin_info(results[0], detailed=True),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # If multiple results, show list
                reply = "Найдено несколько совпадений:\n\n"
                for i, result in enumerate(results[:5], 1):
                    reply += f"{i}. {result['name']}\n"
                reply += "\nВыберите конкретный витамин или минерал для получения подробной информации."
                await update.message.reply_text(reply)
            
            db.update_user_interaction(user_id, "vitamins")
            return
    
    elif is_plant_query(text):
        # Try to find relevant plant care tip
        waste_types = ["яичная скорлупа", "банановая кожура", "кофейная гуща", "чайная заварка"]
        
        for waste in waste_types:
            if waste in text.lower():
                plant_tip = db.get_plant_tip_by_waste(waste)
                if plant_tip:
                    await update.message.reply_text(
                        format_plant_tip(plant_tip, detailed=True),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    db.update_user_interaction(user_id, "plants")
                    return
        
        # If no exact match, try search
        results = db.search_plant_tips(text)
        
        if results:
            if len(results) == 1:
                # If only one result, show detailed info
                await update.message.reply_text(
                    format_plant_tip(results[0], detailed=True),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # If multiple results, show list
                reply = "Найдено несколько советов по уходу за растениями:\n\n"
                for i, result in enumerate(results[:5], 1):
                    reply += f"{i}. {result['waste_type']}\n"
                reply += "\nВыберите конкретный тип отходов для получения подробной информации."
                await update.message.reply_text(reply)
            
            db.update_user_interaction(user_id, "plants")
            return
    
    # If we got here, use AI to attempt to answer the question
    await handle_ai_general_question(update, context, text)


async def show_vitamins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show vitamins menu"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🍏 *Витамины и минералы*\n\nВыберите интересующий вас витамин или минерал:",
            reply_markup=get_vitamins_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🍏 *Витамины и минералы*\n\nВыберите интересующий вас витамин или минерал:",
            reply_markup=get_vitamins_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    user_id = update.effective_user.id
    db.update_user_interaction(user_id, "vitamins")


async def show_plants_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show plants menu"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🌱 *Уход за растениями*\n\nВыберите тип бытовых отходов для получения информации:",
            reply_markup=get_plants_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🌱 *Уход за растениями*\n\nВыберите тип бытовых отходов для получения информации:",
            reply_markup=get_plants_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    user_id = update.effective_user.id
    db.update_user_interaction(user_id, "plants")


async def show_ai_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the AI menu"""
    user_id = update.effective_user.id
    
    # Track user interaction
    db.update_user_interaction(user_id, "ai_menu")
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🤖 *PLEXY - Ваш консультант*\n\nКак я могу вам помочь сегодня?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_ai_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "🤖 *PLEXY - Ваш консультант*\n\nКак я могу вам помочь сегодня?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_ai_menu_keyboard()
        )


async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ menu"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❓ *Часто задаваемые вопросы*\n\nВыберите интересующий вас раздел:",
            reply_markup=get_faq_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❓ *Часто задаваемые вопросы*\n\nВыберите интересующий вас раздел:",
            reply_markup=get_faq_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    user_id = update.effective_user.id
    db.update_user_interaction(user_id, "faq")


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start feedback conversation"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📝 *Обратная связь*\n\n"
            "Пожалуйста, напишите ваше предложение, замечание или пожелание. "
            "Это поможет нам улучшить бота.\n\n"
            "Чтобы отменить, отправьте /cancel",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "📝 *Обратная связь*\n\n"
            "Пожалуйста, напишите ваше предложение, замечание или пожелание. "
            "Это поможет нам улучшить бота.\n\n"
            "Чтобы отменить, отправьте /cancel",
            parse_mode=ParseMode.MARKDOWN
        )
    
    return FEEDBACK


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the feedback"""
    user_id = update.effective_user.id
    feedback_text = update.message.text
    
    # Save feedback to database
    db.add_feedback(user_id, feedback_text)
    
    await update.message.reply_text(
        "Спасибо за ваш отзыв! Мы обязательно учтем его при улучшении бота.",
        reply_markup=get_main_menu_keyboard()
    )
    
    return ConversationHandler.END


async def cancel_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel feedback conversation"""
    await update.message.reply_text(
        "Отправка отзыва отменена.",
        reply_markup=get_main_menu_keyboard()
    )
    
    return ConversationHandler.END


async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel any ongoing operation"""
    query = update.callback_query
    await query.answer()
    
    # Clear state
    if 'state' in context.user_data:
        del context.user_data['state']
    
    await query.edit_message_text(
        "Операция отменена. Чем еще я могу помочь?",
        reply_markup=None
    )


async def start_ai_general_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI general question conversation"""
    context.user_data['state'] = WAITING_FOR_GENERAL_QUESTION
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "💬 *Задайте вопрос PLEXY*\n\n"
            "Задайте любой вопрос о витаминах, растениях или здоровье, "
            "и я постараюсь дать точный и полезный ответ.\n\n"
            "Напишите ваш вопрос:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    else:
        await update.message.reply_text(
            "💬 *Задайте вопрос PLEXY*\n\n"
            "Задайте любой вопрос о витаминах, растениях или здоровье, "
            "и я постараюсь дать точный и полезный ответ.\n\n"
            "Напишите ваш вопрос:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    
    return WAITING_FOR_GENERAL_QUESTION


async def handle_ai_general_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question=None) -> None:
    """Handle general AI questions"""
    user_id = update.effective_user.id
    user_question = question or update.message.text
    
    # Track user interaction
    db.update_user_interaction(user_id, "ai_question", user_question)
    
    # Send "typing" indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Get response from AI service
        response = await ai_service.get_ai_response(user_question)
        
        # Clean any markdown to ensure proper formatting
        response = clean_markdown(response)
        
        # Send the response
        await update.message.reply_text(
            response,
            reply_markup=get_ai_menu_keyboard()
        )
    except Exception as e:
        logging.error(f"Error getting AI response: {str(e)}")
        await update.message.reply_text(
            "❌ Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте переформулировать вопрос или повторите попытку позже.",
            reply_markup=get_ai_menu_keyboard()
        )


async def start_ai_vitamin_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI vitamin recommendation conversation"""
    context.user_data['state'] = WAITING_FOR_VITAMIN_QUERY
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "💊 *Рекомендация витаминов*\n\n"
            "Опишите ваш запрос, симптомы или состояние, и искусственный интеллект "
            "предложит подходящие витамины и минералы.\n\n"
            "Например: 'Какие витамины нужны при авитаминозе' или 'Что принимать для повышения иммунитета'.\n\n"
            "Напишите ваш запрос:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    else:
        await update.message.reply_text(
            "💊 *Рекомендация витаминов*\n\n"
            "Опишите ваш запрос, симптомы или состояние, и искусственный интеллект "
            "предложит подходящие витамины и минералы.\n\n"
            "Например: 'Какие витамины нужны при авитаминозе' или 'Что принимать для повышения иммунитета'.\n\n"
            "Напишите ваш запрос:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    
    return WAITING_FOR_VITAMIN_QUERY


async def handle_ai_vitamin_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> None:
    """Handle AI vitamin recommendation"""
    if not query:
        query = update.message.text
    
    # Clear state
    if 'state' in context.user_data:
        del context.user_data['state']
    
    # Send typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    # Get response from AI
    response = await ai_service.recommend_vitamins(query)
    
    # Clean response to ensure proper formatting
    response = clean_markdown(response)
    
    # Send response
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
        parse_mode=ParseMode.MARKDOWN
    )


async def start_ai_plant_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start AI plant analysis conversation"""
    context.user_data['state'] = WAITING_FOR_PLANT_IMAGE
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📷 *Анализ растения*\n\n"
            "Отправьте фотографию растения, и искусственный интеллект:"
            "\n- Определит вид растения"
            "\n- Оценит его состояние"
            "\n- Даст рекомендации по уходу"
            "\n- Расскажет о плюсах и минусах его выращивания\n\n"
            "Отправьте фотографию:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    else:
        await update.message.reply_text(
            "📷 *Анализ растения*\n\n"
            "Отправьте фотографию растения, и искусственный интеллект:"
            "\n- Определит вид растения"
            "\n- Оценит его состояние"
            "\n- Даст рекомендации по уходу"
            "\n- Расскажет о плюсах и минусах его выращивания\n\n"
            "Отправьте фотографию:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    
    return WAITING_FOR_PLANT_IMAGE


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user photos"""
    user_id = update.effective_user.id
    
    # Get best quality photo
    photo_file = await update.message.photo[-1].get_file()
    
    # Create temp directory if it doesn't exist
    if not os.path.exists("temp"):
        os.makedirs("temp")
    
    # Define file paths
    file_path = f"temp/photo_{user_id}.jpg"
    
    # Download photo
    await photo_file.download_to_drive(file_path)
    
    # Track user interaction
    db.update_user_interaction(user_id, "photo_recognition")
    
    # Always process as plant identification
    processing_message = await update.message.reply_text("🔍 PLEXY анализирует вашу фотографию растения...")
    
    try:
        # Get plant recognition from the service
        plant_info = await ai_service.recognize_plant(file_path)
        
        if not plant_info or "error" in plant_info:
            # If recognition failed
            await processing_message.edit_text(
                "❌ Не удалось распознать растение на фотографии. Пожалуйста, убедитесь, что растение хорошо видно и попробуйте снова.",
                reply_markup=get_plants_menu_keyboard()
            )
            return
        
        # Extract plant details
        plant_name = plant_info.get("name", "Неизвестное растение")
        scientific_name = plant_info.get("scientific_name", "Научное название не найдено")
        
        # Clean text to ensure proper formatting
        description = clean_markdown(plant_info.get("description", ""))
        care_tips = clean_markdown(plant_info.get("care_tips", ""))
        
        # Check if we have specific details about the plant
        has_specific_info = (
            plant_name != "Неизвестное растение" and 
            scientific_name != "Научное название не найдено" and
            description and care_tips
        )
        
        # Format information for display
        plant_details = []
        
        # Always show name and scientific name first
        plant_details.append(f"*Название:* {plant_name}")
        plant_details.append(f"*Научное название:* {scientific_name}")
        
        # Add state information if available
        if "state" in plant_info and plant_info["state"] and plant_info["state"] != "Состояние не определено":
            state_info = clean_markdown(plant_info["state"])
            plant_details.append(f"\n*Состояние растения:*\n{state_info}")
        
        # Add description
        if description:
            # Check for redundancy - don't add if it's too similar to state
            if not "state" in plant_info or description != plant_info["state"]:
                plant_details.append(f"\n*Описание:*\n{description}")
        
        # Add care tips with good formatting
        if care_tips:
            plant_details.append(f"\n*Советы по уходу:*\n{care_tips}")
        
        # Add light requirements if available
        if "light" in plant_info and plant_info["light"] and plant_info["light"] != "Нет информации":
            light_info = clean_markdown(plant_info["light"])
            plant_details.append(f"\n*Освещение:*\n{light_info}")
        
        # Add watering info if available
        if "water" in plant_info and plant_info["water"] and plant_info["water"] != "Нет информации":
            water_info = clean_markdown(plant_info["water"])
            plant_details.append(f"\n*Полив:*\n{water_info}")
        
        # Add temperature info if available
        if "temperature" in plant_info and plant_info["temperature"] and plant_info["temperature"] != "Нет информации":
            temp_info = clean_markdown(plant_info["temperature"])
            plant_details.append(f"\n*Температура:*\n{temp_info}")
        
        # Add soil info if available
        if "soil" in plant_info and plant_info["soil"] and plant_info["soil"] != "Нет информации":
            soil_info = clean_markdown(plant_info["soil"])
            plant_details.append(f"\n*Почва:*\n{soil_info}")
        
        # Add common problems if available
        if "problems" in plant_info and plant_info["problems"] and plant_info["problems"] != "Нет информации":
            problems_info = clean_markdown(plant_info["problems"])
            plant_details.append(f"\n*Распространенные проблемы:*\n{problems_info}")
        
        # Format the final plant information text
        if has_specific_info:
            header = "🌿 *Растение найдено!*\n\n"
        else:
            header = "🌿 *Растение найдено!*\n\n"
            
            if plant_name == "Неизвестное растение":
                header = "🌿 *Растение не определено*\n\nНе удалось точно определить вид растения, но вот общие рекомендации:\n\n"
        
        plant_info_text = header + "\n".join(plant_details)
        
        # Make sure the message isn't too long for Telegram
        if len(plant_info_text) > 4000:
            plant_info_text = plant_info_text[:3900] + "\n\n... (текст сокращен из-за ограничений Telegram)"
        
        # Delete processing message and send the result
        await processing_message.delete()
        await update.message.reply_text(
            plant_info_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_plant_actions_keyboard(plant_name) if plant_name != "Неизвестное растение" else get_plants_menu_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error in plant recognition: {str(e)}")
        await processing_message.edit_text(
            "❌ Произошла ошибка при анализе фотографии. Пожалуйста, попробуйте ещё раз позже.",
            reply_markup=get_main_menu_keyboard()
        )
    
    # Clean up - remove temporary file
    if os.path.exists(file_path):
        os.remove(file_path)


async def show_problems_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show problems and solutions menu"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔍 *Проблемы и решения*\n\nВыберите категорию проблем или опишите свою проблему для получения рекомендаций:",
            reply_markup=get_problems_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🔍 *Проблемы и решения*\n\nВыберите категорию проблем или опишите свою проблему для получения рекомендаций:",
            reply_markup=get_problems_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    user_id = update.effective_user.id
    db.update_user_interaction(user_id, "problems_solutions")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = update.effective_user.id
    
    # Cancel operation
    if callback_data == "cancel_operation":
        return await cancel_operation(update, context)
    
    # Main menu navigation
    if callback_data == "main_menu":
        await query.edit_message_text(
            "Выберите интересующий вас раздел или задайте вопрос:",
            reply_markup=get_main_menu_keyboard()
        )
    
    # Handle feedback
    elif callback_data == "feedback":
        return await start_feedback(update, context)
    
    # Vitamins section
    elif callback_data == "vitamins_menu":
        await show_vitamins_menu(update, context)
    
    elif callback_data == "vitamins_all":
        vitamins = db.get_all_vitamins()
        text = "*Список витаминов и минералов:*\n\n"
        
        for vitamin in vitamins:
            text += f"• {vitamin['name']}: {vitamin['short_description']}\n\n"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("vitamins_menu")
        )
        db.update_user_interaction(user_id, "vitamins")
    
    elif callback_data.startswith("vitamin_"):
        # Extract vitamin name
        name = "Витамин " + callback_data[8:].upper()
        
        vitamin = db.get_vitamin_by_name(name)
        
        if vitamin:
            await query.edit_message_text(
                format_vitamin_info(vitamin, detailed=True),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_keyboard("vitamins_menu")
            )
        else:
            await query.edit_message_text(
                f"Информация о {name} не найдена.",
                reply_markup=get_back_keyboard("vitamins_menu")
            )
        
        db.update_user_interaction(user_id, "vitamins")
        
    elif callback_data.startswith("mineral_"):
        # Extract mineral name
        name = callback_data[8:].capitalize()
        
        vitamin = db.get_vitamin_by_name(name)
        
        if vitamin:
            await query.edit_message_text(
                format_vitamin_info(vitamin, detailed=True),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_keyboard("vitamins_menu")
            )
        else:
            await query.edit_message_text(
                f"Информация о минерале {name} не найдена.",
                reply_markup=get_back_keyboard("vitamins_menu")
            )
        
        db.update_user_interaction(user_id, "vitamins")
    
    # Plants section
    elif callback_data == "plants_menu":
        await show_plants_menu(update, context)
    
    elif callback_data == "plants_all":
        plant_tips = db.get_all_plant_tips()
        text = "*Способы использования бытовых отходов для растений:*\n\n"
        
        for tip in plant_tips:
            text += f"• {tip['waste_type']}: {tip['short_description']}\n\n"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("plants_menu")
        )
        db.update_user_interaction(user_id, "plants")
    
    # Handle plant-specific actions
    elif callback_data.startswith("plant_info_"):
        # Extract plant name from callback data
        plant_name = callback_data[11:]  # Remove "plant_info_" prefix
        
        # Try to get plant from database
        plant = db.get_plant_by_name(plant_name)
        
        if plant:
            # Format plant information
            plant_text = f"🌿 *{plant['name']}*\n\n"
            
            if 'scientific_name' in plant and plant['scientific_name']:
                plant_text += f"*Научное название:* {plant['scientific_name']}\n\n"
            
            if 'description' in plant and plant['description']:
                plant_text += f"*Описание:*\n{plant['description']}\n\n"
            
            if 'care_tips' in plant and plant['care_tips']:
                plant_text += f"*Рекомендации по уходу:*\n{plant['care_tips']}\n\n"
            
            if 'extra_data' in plant:
                extra = plant['extra_data']
                
                if 'light' in extra:
                    plant_text += f"*Освещение:*\n{extra['light']}\n\n"
                
                if 'watering' in extra:
                    plant_text += f"*Полив:*\n{extra['watering']}\n\n"
                
                if 'temperature' in extra:
                    plant_text += f"*Температура:*\n{extra['temperature']}\n\n"
                
                if 'soil' in extra:
                    plant_text += f"*Почва:*\n{extra['soil']}\n\n"
            
            await query.edit_message_text(
                plant_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_plant_actions_keyboard(plant_name)
            )
        else:
            # If plant not in database, use AI to get information
            prompt = f"Дай информацию о растении {plant_name}. Включи научное название, описание, особенности."
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            try:
                response = await ai_service.generate_response(prompt, max_tokens=800)
                response = clean_markdown(response)
                
                await query.edit_message_text(
                    f"🌿 *Информация о растении*\n\n{response}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
            except Exception as e:
                logging.error(f"Error getting plant info: {e}")
                await query.edit_message_text(
                    f"Не удалось получить подробную информацию о растении {plant_name}.",
                    reply_markup=get_plants_menu_keyboard()
                )
        
        db.update_user_interaction(user_id, "plant_info", plant_name)
    
    elif callback_data.startswith("plant_water_"):
        # Extract plant name from callback data
        plant_name = callback_data[12:]  # Remove "plant_water_" prefix
        
        # Try to get plant from database
        plant = db.get_plant_by_name(plant_name)
        watering_info = None
        
        if plant and 'extra_data' in plant and 'watering' in plant['extra_data']:
            watering_info = plant['extra_data']['watering']
        
        if watering_info:
            await query.edit_message_text(
                f"💧 *Полив для {plant_name}*\n\n{watering_info}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_plant_actions_keyboard(plant_name)
            )
        else:
            # If watering info not in database, use AI to get information
            prompt = f"Как правильно поливать растение {plant_name}? Дай подробные рекомендации по поливу."
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            try:
                response = await ai_service.generate_response(prompt, max_tokens=500)
                response = clean_markdown(response)
                
                await query.edit_message_text(
                    f"💧 *Полив для {plant_name}*\n\n{response}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
            except Exception as e:
                logging.error(f"Error getting watering info: {e}")
                await query.edit_message_text(
                    f"Не удалось получить информацию о поливе для {plant_name}.",
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
        
        db.update_user_interaction(user_id, "plant_water", plant_name)
    
    elif callback_data.startswith("plant_light_"):
        # Extract plant name from callback data
        plant_name = callback_data[12:]  # Remove "plant_light_" prefix
        
        # Try to get plant from database
        plant = db.get_plant_by_name(plant_name)
        light_info = None
        
        if plant and 'extra_data' in plant and 'light' in plant['extra_data']:
            light_info = plant['extra_data']['light']
        
        if light_info:
            await query.edit_message_text(
                f"☀️ *Освещение для {plant_name}*\n\n{light_info}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_plant_actions_keyboard(plant_name)
            )
        else:
            # If light info not in database, use AI to get information
            prompt = f"Какое освещение требуется для растения {plant_name}? Дай подробные рекомендации."
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            try:
                response = await ai_service.generate_response(prompt, max_tokens=500)
                response = clean_markdown(response)
                
                await query.edit_message_text(
                    f"☀️ *Освещение для {plant_name}*\n\n{response}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
            except Exception as e:
                logging.error(f"Error getting light info: {e}")
                await query.edit_message_text(
                    f"Не удалось получить информацию об освещении для {plant_name}.",
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
        
        db.update_user_interaction(user_id, "plant_light", plant_name)
    
    elif callback_data.startswith("plant_temp_"):
        # Extract plant name from callback data
        plant_name = callback_data[11:]  # Remove "plant_temp_" prefix
        
        # Try to get plant from database
        plant = db.get_plant_by_name(plant_name)
        temp_info = None
        
        if plant and 'extra_data' in plant and 'temperature' in plant['extra_data']:
            temp_info = plant['extra_data']['temperature']
        
        if temp_info:
            await query.edit_message_text(
                f"🌡️ *Температура для {plant_name}*\n\n{temp_info}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_plant_actions_keyboard(plant_name)
            )
        else:
            # If temperature info not in database, use AI to get information
            prompt = f"Какая температура требуется для растения {plant_name}? Дай подробные рекомендации."
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            try:
                response = await ai_service.generate_response(prompt, max_tokens=500)
                response = clean_markdown(response)
                
                await query.edit_message_text(
                    f"🌡️ *Температура для {plant_name}*\n\n{response}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
            except Exception as e:
                logging.error(f"Error getting temperature info: {e}")
                await query.edit_message_text(
                    f"Не удалось получить информацию о температуре для {plant_name}.",
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
        
        db.update_user_interaction(user_id, "plant_temperature", plant_name)
    
    elif callback_data.startswith("plant_soil_"):
        # Extract plant name from callback data
        plant_name = callback_data[11:]  # Remove "plant_soil_" prefix
        
        # Try to get plant from database
        plant = db.get_plant_by_name(plant_name)
        soil_info = None
        
        if plant and 'extra_data' in plant and 'soil' in plant['extra_data']:
            soil_info = plant['extra_data']['soil']
        
        if soil_info:
            await query.edit_message_text(
                f"🌱 *Почва для {plant_name}*\n\n{soil_info}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_plant_actions_keyboard(plant_name)
            )
        else:
            # If soil info not in database, use AI to get information
            prompt = f"Какая почва требуется для растения {plant_name}? Дай подробные рекомендации."
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            try:
                response = await ai_service.generate_response(prompt, max_tokens=500)
                response = clean_markdown(response)
                
                await query.edit_message_text(
                    f"🌱 *Почва для {plant_name}*\n\n{response}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
            except Exception as e:
                logging.error(f"Error getting soil info: {e}")
                await query.edit_message_text(
                    f"Не удалось получить информацию о почве для {plant_name}.",
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
        
        db.update_user_interaction(user_id, "plant_soil", plant_name)
    
    elif callback_data.startswith("plant_problems_"):
        # Extract plant name from callback data
        plant_name = callback_data[15:]  # Remove "plant_problems_" prefix
        
        # Try to get plant from database
        plant = db.get_plant_by_name(plant_name)
        problems_info = None
        
        if plant and 'extra_data' in plant and 'common_problems' in plant['extra_data']:
            problems_info = plant['extra_data']['common_problems']
        
        if problems_info:
            await query.edit_message_text(
                f"🩺 *Проблемы и болезни {plant_name}*\n\n{problems_info}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_plant_actions_keyboard(plant_name)
            )
        else:
            # If problems info not in database, use AI to get information
            prompt = f"Какие распространенные проблемы и болезни бывают у растения {plant_name}? Дай подробное описание и методы лечения."
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            
            try:
                response = await ai_service.generate_response(prompt, max_tokens=600)
                response = clean_markdown(response)
                
                await query.edit_message_text(
                    f"🩺 *Проблемы и болезни {plant_name}*\n\n{response}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
            except Exception as e:
                logging.error(f"Error getting problems info: {e}")
                await query.edit_message_text(
                    f"Не удалось получить информацию о проблемах для {plant_name}.",
                    reply_markup=get_plant_actions_keyboard(plant_name)
                )
        
        db.update_user_interaction(user_id, "plant_problems", plant_name)
    
    elif callback_data.startswith("waste_"):
        waste_type = callback_data[6:].replace("_", " ")
        
        if waste_type == "eggshell":
            waste_type = "яичная скорлупа"
        elif waste_type == "banana":
            waste_type = "банановая кожура"
        elif waste_type == "coffee":
            waste_type = "кофейная гуща"
        elif waste_type == "tea":
            waste_type = "чайная заварка"
        
        plant_tip = db.get_plant_tip_by_waste(waste_type)
        
        if plant_tip:
            await query.edit_message_text(
                format_plant_tip(plant_tip, detailed=True),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_keyboard("plants_menu")
            )
        else:
            await query.edit_message_text(
                f"Информация о использовании {waste_type} не найдена.",
                reply_markup=get_back_keyboard("plants_menu")
            )
        
        db.update_user_interaction(user_id, "plants")
    
    # AI Consultant section
    elif callback_data == "ai_consultant_menu":
        await show_ai_menu(update, context)
    
    elif callback_data == "ai_general_question":
        return await start_ai_general_question(update, context)
    
    elif callback_data == "ai_vitamin_recommend":
        return await start_ai_vitamin_recommendation(update, context)
    
    elif callback_data == "ai_plant_analysis":
        return await start_ai_plant_analysis(update, context)
    
    # FAQ section
    elif callback_data.startswith("faq_"):
        faq_id = callback_data[4:]
        faq_text = format_faq(faq_id)
        
        if faq_text:
            await query.edit_message_text(
                faq_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_keyboard("faq_menu")
            )
        else:
            await query.edit_message_text(
                "Информация не найдена.",
                reply_markup=get_back_keyboard("faq_menu")
            )
        
        db.update_user_interaction(user_id, "faq")
        
    elif callback_data == "faq_menu":
        await show_faq(update, context)
    
    # Problems section
    elif callback_data == "problems_menu":
        await show_problems_menu(update, context)
    elif callback_data in ["vitamin_problems", "plant_problems"]:
        context.user_data['problem_type'] = "vitamin" if callback_data == "vitamin_problems" else "plant"
        return await start_problem_description(update, context)


async def start_problem_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start problem description conversation"""
    problem_type = context.user_data.get('problem_type', 'general')
    context.user_data['state'] = WAITING_FOR_PROBLEM_DESCRIPTION
    
    if update.callback_query:
        await update.callback_query.answer()
        if problem_type == "vitamin":
            message = (
                "🔍 *Проблемы с витаминами*\n\n"
                "Опишите вашу проблему, связанную с витаминами или минералами. Например:\n"
                "- Побочные эффекты от приема витаминов\n"
                "- Симптомы дефицита витаминов\n"
                "- Вопросы о дозировке\n\n"
                "Опишите вашу проблему:"
            )
        elif problem_type == "plant":
            message = (
                "🔍 *Проблемы с растениями*\n\n"
                "Опишите вашу проблему, связанную с комнатными растениями. Например:\n"
                "- Желтеют листья\n"
                "- Не цветет растение\n"
                "- Проблемы с поливом\n\n"
                "Опишите вашу проблему:"
            )
        else:
            message = (
                "🔍 *Анализ проблемы*\n\n"
                "Опишите вашу проблему, и AI поможет найти решение:\n\n"
                "Опишите вашу проблему:"
            )
        
        await update.callback_query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    else:
        if problem_type == "vitamin":
            message = (
                "🔍 *Проблемы с витаминами*\n\n"
                "Опишите вашу проблему, связанную с витаминами или минералами. Например:\n"
                "- Побочные эффекты от приема витаминов\n"
                "- Симптомы дефицита витаминов\n"
                "- Вопросы о дозировке\n\n"
                "Опишите вашу проблему:"
            )
        elif problem_type == "plant":
            message = (
                "🔍 *Проблемы с растениями*\n\n"
                "Опишите вашу проблему, связанную с комнатными растениями. Например:\n"
                "- Желтеют листья\n"
                "- Не цветет растение\n"
                "- Проблемы с поливом\n\n"
                "Опишите вашу проблему:"
            )
        else:
            message = (
                "🔍 *Анализ проблемы*\n\n"
                "Опишите вашу проблему, и AI поможет найти решение:\n\n"
                "Опишите вашу проблему:"
            )
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
    
    return WAITING_FOR_PROBLEM_DESCRIPTION


async def handle_problem_description(update: Update, context: ContextTypes.DEFAULT_TYPE, description=None) -> None:
    """Handle problem description"""
    if not description:
        description = update.message.text
    
    problem_type = context.user_data.get('problem_type', 'general')
    
    # Clear state
    if 'state' in context.user_data:
        del context.user_data['state']
    if 'problem_type' in context.user_data:
        del context.user_data['problem_type']
    
    # Send typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    # Get response from AI
    analysis = await ai_service.identify_problem(description, problem_type)
    
    # Format analysis
    formatted_analysis = format_problem_analysis(analysis, problem_type)
    
    # Clean response to ensure proper formatting
    formatted_analysis = clean_markdown(formatted_analysis)
    
    # Send analysis
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_analysis,
        parse_mode=ParseMode.MARKDOWN
    )


async def main() -> None:
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("vitamins", show_vitamins_menu))
    application.add_handler(CommandHandler("plants", show_plants_menu))
    application.add_handler(CommandHandler("ai", show_ai_menu))
    application.add_handler(CommandHandler("feedback", start_feedback))
    
    # Add feedback conversation handler
    feedback_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("feedback", start_feedback),
            MessageHandler(filters.Regex(r'^📝 Обратная связь$'), start_feedback)
        ],
        states={
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)]
        },
        fallbacks=[CommandHandler("cancel", cancel_feedback)]
    )
    application.add_handler(feedback_conv_handler)
    
    # Add photo handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add message handler (for text messages)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Start the bot with polling
    logging.info("Bot started")
    
    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logging.info("PLEXY бот запущен и готов к работе! Нажмите Ctrl+C для остановки.")
    
    # Run the bot until the user presses Ctrl+C
    # Create a future that will be set when a signal is received
    stop_signal = asyncio.Future()
    
    # Windows-compatible signal handling
    def signal_handler(sig, frame):
        logging.info(f"Получен сигнал {sig}, останавливаю бота...")
        stop_signal.set_result(None)
    
    # Use the standard signal module for Windows compatibility
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await stop_signal
    finally:
        # Stop the bot
        logging.info("Останавливаю бота...")
        await application.stop()
        logging.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())