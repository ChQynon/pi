import logging
import os
import re
import json
import time
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, ChatActions, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply, ChatAction
from aiogram.utils.callback_data import CallbackData

from config import BOT_TOKEN, CHUTES_API_TOKEN
from ai_service import AIService
from utils import format_vitamin_info, format_plant_tip, log_user_interaction
from database import Database
from states import UserState

# Add a new handler for plant care tips

@dp.message_handler(commands=['care'])
async def cmd_plant_care(message: types.Message):
    """Handle /care command to get plant care information"""
    # Extract plant name from command
    args = message.get_args()
    if not args:
        await message.reply(
            "Пожалуйста, укажите название растения после команды.\n"
            "Например: /care Монстера",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Get user language
    user_id = message.from_user.id
    language = "ru"  # Default language
    
    # Send typing action
    await message.answer_chat_action(ChatAction.TYPING)
    
    # Get plant care tips
    plant_name = args
    ai_service = AIService()
    care_response = await ai_service.get_plant_care_tips(plant_name)
    
    if care_response["found"]:
        # Create nicely formatted message
        reply_text = f"🌱 *{care_response['name']}*\n\n"
        
        # Add emoji to each section
        reply_text += f"💧 *Полив:* {care_response['care_tips']['watering']}\n\n"
        reply_text += f"☀️ *Освещение:* {care_response['care_tips']['light']}\n\n"
        reply_text += f"🌡️ *Температура:* {care_response['care_tips']['temperature']}\n\n"
        reply_text += f"🌱 *Почва:* {care_response['care_tips']['soil']}\n\n"
        
        if care_response['care_tips'].get('humidity'):
            reply_text += f"💦 *Влажность:* {care_response['care_tips']['humidity']}\n\n"
        
        if care_response['care_tips'].get('fertilizing'):
            reply_text += f"🧪 *Удобрение:* {care_response['care_tips']['fertilizing']}\n\n"
        
        # Common problems
        if care_response.get('common_problems'):
            reply_text += "⚠️ *Распространенные проблемы:*\n"
            for problem in care_response['common_problems']:
                reply_text += f"• {problem}\n"
            reply_text += "\n"
        
        # Helpful tips
        if care_response.get('tips'):
            reply_text += "💡 *Полезные советы:*\n"
            for tip in care_response['tips']:
                reply_text += f"• {tip}\n"
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🔍 Другое растение", callback_data=f"new_plant_care"),
            InlineKeyboardButton("👍 Спасибо!", callback_data=f"thanks_care_{care_response['name']}")
        )
        
        await message.reply(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    else:
        # Plant not found
        reply_text = f"{care_response['message']}\n\n"
        for i, tip in enumerate(care_response['generic_tips'], 1):
            reply_text += f"{i}. {tip}\n"
        
        # Create keyboard for not found
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔍 Искать другое растение", callback_data="new_plant_care"))
        
        await message.reply(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    
    # Log user interaction
    log_user_interaction(message.from_user, "plant_care", plant_name)


@dp.callback_query_handler(lambda c: c.data == "new_plant_care")
async def callback_new_plant_care(callback_query: types.CallbackQuery):
    """Handle request for information about a different plant"""
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "Пожалуйста, введите название растения, о котором хотите узнать:",
        reply_markup=ForceReply(selective=True)
    )
    
    # Set user state to waiting for plant name
    await UserState.waiting_for_plant_name.set()
    
    # Store the original message to link replies
    state = dp.current_state(user=callback_query.from_user.id)
    await state.update_data(original_message_id=callback_query.message.message_id)


@dp.message_handler(state=UserState.waiting_for_plant_name)
async def process_plant_name(message: types.Message, state: FSMContext):
    """Process plant name from user"""
    plant_name = message.text.strip()
    
    # Clear state
    await state.finish()
    
    # Send typing action
    await message.answer_chat_action(ChatAction.TYPING)
    
    # Get plant care tips
    ai_service = AIService()
    care_response = await ai_service.get_plant_care_tips(plant_name)
    
    if care_response["found"]:
        # Create nicely formatted message
        reply_text = f"🌱 *{care_response['name']}*\n\n"
        
        # Add emoji to each section
        reply_text += f"💧 *Полив:* {care_response['care_tips']['watering']}\n\n"
        reply_text += f"☀️ *Освещение:* {care_response['care_tips']['light']}\n\n"
        reply_text += f"🌡️ *Температура:* {care_response['care_tips']['temperature']}\n\n"
        reply_text += f"🌱 *Почва:* {care_response['care_tips']['soil']}\n\n"
        
        if care_response['care_tips'].get('humidity'):
            reply_text += f"💦 *Влажность:* {care_response['care_tips']['humidity']}\n\n"
        
        if care_response['care_tips'].get('fertilizing'):
            reply_text += f"🧪 *Удобрение:* {care_response['care_tips']['fertilizing']}\n\n"
        
        # Common problems
        if care_response.get('common_problems'):
            reply_text += "⚠️ *Распространенные проблемы:*\n"
            for problem in care_response['common_problems']:
                reply_text += f"• {problem}\n"
            reply_text += "\n"
        
        # Helpful tips
        if care_response.get('tips'):
            reply_text += "💡 *Полезные советы:*\n"
            for tip in care_response['tips']:
                reply_text += f"• {tip}\n"
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🔍 Другое растение", callback_data=f"new_plant_care"),
            InlineKeyboardButton("👍 Спасибо!", callback_data=f"thanks_care_{care_response['name']}")
        )
        
        await message.reply(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    else:
        # Plant not found
        reply_text = f"{care_response['message']}\n\n"
        for i, tip in enumerate(care_response['generic_tips'], 1):
            reply_text += f"{i}. {tip}\n"
        
        # Create keyboard for not found
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔍 Искать другое растение", callback_data="new_plant_care"))
        
        await message.reply(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    
    # Log user interaction
    log_user_interaction(message.from_user, "plant_care", plant_name) 