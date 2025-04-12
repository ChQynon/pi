from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Main menu keyboard
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🍏 Витамины и минералы", callback_data="vitamins_menu")],
        [InlineKeyboardButton("🌱 Уход за растениями", callback_data="plants_menu")],
        [InlineKeyboardButton("🤖 AI Консультант", callback_data="ai_consultant_menu")],
        [InlineKeyboardButton("🔍 Проблемы и решения", callback_data="problems_menu")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq_menu")],
        [InlineKeyboardButton("📝 Обратная связь", callback_data="feedback")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Vitamins menu keyboard
def get_vitamins_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Все витамины и минералы", callback_data="vitamins_all")],
        [
            InlineKeyboardButton("Витамин A", callback_data="vitamin_a"),
            InlineKeyboardButton("Витамин C", callback_data="vitamin_c")
        ],
        [
            InlineKeyboardButton("Витамин D", callback_data="vitamin_d"),
            InlineKeyboardButton("Витамин E", callback_data="vitamin_e")
        ],
        [
            InlineKeyboardButton("Кальций", callback_data="mineral_calcium"),
            InlineKeyboardButton("Магний", callback_data="mineral_magnesium")
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Plants menu keyboard
def get_plants_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Все советы по уходу", callback_data="plants_all")],
        [
            InlineKeyboardButton("Яичная скорлупа", callback_data="waste_eggshell"),
            InlineKeyboardButton("Банановая кожура", callback_data="waste_banana")
        ],
        [
            InlineKeyboardButton("Кофейная гуща", callback_data="waste_coffee"),
            InlineKeyboardButton("Чайная заварка", callback_data="waste_tea")
        ],
        [InlineKeyboardButton("🔍 Поиск советов", callback_data="plants_search")],
        [InlineKeyboardButton("📷 Анализ растения", callback_data="ai_plant_analysis")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Plant actions keyboard
def get_plant_actions_keyboard(plant_name):
    keyboard = [
        [InlineKeyboardButton("🔍 Подробнее о растении", callback_data=f"plant_info_{plant_name}")],
        [
            InlineKeyboardButton("💧 Полив", callback_data=f"plant_water_{plant_name}"),
            InlineKeyboardButton("☀️ Освещение", callback_data=f"plant_light_{plant_name}")
        ],
        [
            InlineKeyboardButton("🌡️ Температура", callback_data=f"plant_temp_{plant_name}"),
            InlineKeyboardButton("🌱 Почва", callback_data=f"plant_soil_{plant_name}")
        ],
        [InlineKeyboardButton("🩺 Проблемы и болезни", callback_data=f"plant_problems_{plant_name}")],
        [InlineKeyboardButton("📝 Другие советы по уходу", callback_data="plants_menu")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# FAQ keyboard
def get_faq_keyboard():
    keyboard = [
        [InlineKeyboardButton("О боте", callback_data="faq_about")],
        [InlineKeyboardButton("Как искать информацию", callback_data="faq_how_to_search")],
        [InlineKeyboardButton("Источники информации", callback_data="faq_sources")],
        [InlineKeyboardButton("О AI возможностях", callback_data="faq_ai_features")],
        [InlineKeyboardButton("О решении проблем", callback_data="faq_problem_solving")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Back button keyboard
def get_back_keyboard(callback_data="main_menu"):
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)

# AI consultant keyboard
def get_ai_consultant_keyboard():
    keyboard = [
        [InlineKeyboardButton("💬 Общий вопрос", callback_data="ai_general_question")],
        [InlineKeyboardButton("💊 Рекомендация витаминов", callback_data="ai_vitamin_recommend")],
        [InlineKeyboardButton("📷 Анализ растения", callback_data="ai_plant_analysis")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# AI menu keyboard - updated version
def get_ai_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="ai_general_question")],
        [InlineKeyboardButton("💊 Витамины", callback_data="ai_vitamin_recommend")],
        [InlineKeyboardButton("📷 Анализ растения", callback_data="ai_plant_analysis")],
        [InlineKeyboardButton("🌿 Меню растений", callback_data="plants_menu")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Cancel button keyboard
def get_cancel_keyboard():
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_operation")]]
    return InlineKeyboardMarkup(keyboard)

# Problems menu keyboard
def get_problems_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Проблемы с витаминами", callback_data="vitamin_problems")],
        [InlineKeyboardButton("Проблемы с растениями", callback_data="plant_problems")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Problem types keyboard
def get_problem_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("Проблема с витаминами", callback_data="problem_type_vitamin")],
        [InlineKeyboardButton("Проблема с растением", callback_data="problem_type_plant")],
        [InlineKeyboardButton("Другой вопрос", callback_data="problem_type_general")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# More info keyboard
def get_more_info_keyboard(item_id, category):
    keyboard = [
        [InlineKeyboardButton("📚 Подробнее", callback_data=f"more_{category}_{item_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"{category}_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)