import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the plant care tips JSON file
CARE_TIPS_PATH = "data/plant_care_tips.json"

# Ensure the data directory exists
os.makedirs(os.path.dirname(CARE_TIPS_PATH), exist_ok=True)

# Define schemas for different types of care tips
WATERING_SCHEMA = {
    "frequency": str,  # "ежедневно", "раз в неделю", etc.
    "amount": str,  # "умеренно", "обильно", etc.
    "method": str,  # "под корень", "опрыскивание", etc.
    "seasonal_adjustments": Dict[str, str],  # {"зима": "реже", "лето": "чаще"}
}

LIGHT_SCHEMA = {
    "type": str,  # "яркий непрямой", "тень", "полутень", etc.
    "hours": str,  # "6-8 часов", etc.
    "direction": str,  # "южное окно", "северное окно", etc.
    "additional_info": str,  # "избегайте прямых солнечных лучей", etc.
}

SOIL_SCHEMA = {
    "type": str,  # "легкая, рыхлая", "песчаная", etc.
    "ph": str,  # "кислая", "нейтральная", "щелочная", etc.
    "drainage": str,  # "хороший дренаж", etc.
    "composition": str,  # "торф, перлит, песок", etc.
}

FERTILIZER_SCHEMA = {
    "frequency": str,  # "раз в месяц", etc.
    "type": str,  # "универсальное", "для цветущих", etc.
    "strength": str,  # "половинная доза", etc.
    "seasonal": str,  # "весна-лето", etc.
    "special_needs": str,  # "избегайте избытка азота", etc.
}

TEMPERATURE_SCHEMA = {
    "optimal": str,  # "18-24°C", etc.
    "min": str,  # "не ниже 15°C", etc.
    "max": str,  # "не выше 30°C", etc.
    "special_requirements": str,  # "избегайте сквозняков", etc.
}

HUMIDITY_SCHEMA = {
    "optimal": str,  # "высокая", "средняя", etc.
    "methods": List[str],  # ["опрыскивание", "поддон с влажной галькой"], etc.
    "special_requirements": str,  # "регулярно опрыскивайте в жаркую погоду", etc.
}

# Define the plant care tip schema
PLANT_CARE_TIP_SCHEMA = {
    "name": str,  # Название растения
    "scientific_name": str,  # Научное название
    "category": str,  # "комнатное", "садовое", "огородное", etc.
    "description": str,  # Описание растения
    "origin": str,  # Происхождение
    "watering": Dict,  # WATERING_SCHEMA
    "light": Dict,  # LIGHT_SCHEMA
    "soil": Dict,  # SOIL_SCHEMA
    "fertilizer": Dict,  # FERTILIZER_SCHEMA
    "temperature": Dict,  # TEMPERATURE_SCHEMA
    "humidity": Dict,  # HUMIDITY_SCHEMA
    "pruning": str,  # "весной обрезайте старые побеги", etc.
    "propagation": List[str],  # ["черенки", "деление"], etc.
    "common_problems": List[Dict[str, str]],  # [{"название": "...", "решение": "..."}]
    "toxicity": Dict[str, bool],  # {"для_людей": True, "для_животных": True}
    "seasonal_care": Dict[str, str],  # {"весна": "...", "лето": "...", "осень": "...", "зима": "..."}
    "difficulty": str,  # "легкое", "среднее", "сложное"
    "tips": List[str],  # ["защищайте от прямых солнечных лучей", etc.]
    "last_updated": str,  # ISO datetime string
}

# Initial plant care tips data
INITIAL_PLANT_CARE_TIPS = [
    {
        "name": "Фикус каучуконосный",
        "scientific_name": "Ficus elastica",
        "category": "комнатное",
        "description": "Популярное комнатное растение с крупными глянцевыми листьями, неприхотливое в уходе.",
        "origin": "Юго-Восточная Азия",
        "watering": {
            "frequency": "раз в 7-10 дней",
            "amount": "умеренно",
            "method": "когда верхний слой почвы просохнет на 2-3 см",
            "seasonal_adjustments": {"зима": "сократите полив", "лето": "увеличьте при необходимости"}
        },
        "light": {
            "type": "яркий непрямой свет",
            "hours": "6-8 часов в день",
            "direction": "восточное или западное окно",
            "additional_info": "избегайте прямых солнечных лучей, которые могут обжечь листья"
        },
        "soil": {
            "type": "легкая, питательная",
            "ph": "нейтральная или слабокислая",
            "drainage": "хороший дренаж обязателен",
            "composition": "универсальный грунт с добавлением перлита"
        },
        "fertilizer": {
            "frequency": "раз в месяц с весны до осени",
            "type": "универсальное удобрение для комнатных растений",
            "strength": "половинная доза от рекомендуемой",
            "seasonal": "не удобряйте зимой",
            "special_needs": ""
        },
        "temperature": {
            "optimal": "18-24°C",
            "min": "не ниже 12°C",
            "max": "не выше 30°C",
            "special_requirements": "избегайте резких перепадов температуры и сквозняков"
        },
        "humidity": {
            "optimal": "средняя",
            "methods": ["регулярное опрыскивание", "влажная галька в поддоне"],
            "special_requirements": "вытирайте пыль с листьев влажной тряпкой"
        },
        "pruning": "обрезайте верхушку для контроля роста; удаляйте поврежденные листья",
        "propagation": ["верхушечные черенки", "воздушные отводки"],
        "common_problems": [
            {
                "название": "Опадение листьев",
                "решение": "чаще всего из-за переувлажнения или низкой температуры; сократите полив и держите в тепле"
            },
            {
                "название": "Пожелтение листьев",
                "решение": "обычно из-за чрезмерного полива или недостатка питательных веществ"
            },
            {
                "название": "Коричневые пятна на листьях",
                "решение": "часто из-за солнечных ожогов; переместите растение из прямых солнечных лучей"
            }
        ],
        "toxicity": {"для_людей": True, "для_животных": True},
        "seasonal_care": {
            "весна": "начните увеличивать полив и удобрение по мере роста",
            "лето": "регулярное опрыскивание, защита от прямых солнечных лучей",
            "осень": "постепенно сокращайте полив и удобрение",
            "зима": "редкий полив, без удобрений, защита от холодных сквозняков"
        },
        "difficulty": "легкое",
        "tips": [
            "Протирайте листья влажной тряпкой для удаления пыли и сохранения блеска",
            "При обрезке выделяется млечный сок, который может вызвать раздражение кожи, поэтому используйте перчатки",
            "Поворачивайте растение каждые 2-3 недели для равномерного роста"
        ],
        "last_updated": datetime.now().isoformat()
    },
    {
        "name": "Монстера",
        "scientific_name": "Monstera deliciosa",
        "category": "комнатное",
        "description": "Крупное тропическое растение с характерными разрезными листьями, популярное в домашнем озеленении.",
        "origin": "Центральная Америка",
        "watering": {
            "frequency": "раз в неделю",
            "amount": "умеренно",
            "method": "когда верхний слой почвы подсохнет",
            "seasonal_adjustments": {"зима": "сократите полив", "лето": "следите за влажностью почвы"}
        },
        "light": {
            "type": "яркий непрямой свет",
            "hours": "6-8 часов в день",
            "direction": "восточное или северное окно",
            "additional_info": "может переносить небольшое количество прямого солнца утром"
        },
        "soil": {
            "type": "рыхлая, питательная",
            "ph": "слабокислая",
            "drainage": "отличный дренаж",
            "composition": "универсальный грунт с добавлением перлита и кокосового волокна"
        },
        "fertilizer": {
            "frequency": "раз в 2-4 недели с весны до осени",
            "type": "удобрение для лиственных растений",
            "strength": "по инструкции",
            "seasonal": "не удобряйте зимой",
            "special_needs": ""
        },
        "temperature": {
            "optimal": "18-27°C",
            "min": "не ниже 15°C",
            "max": "не выше 32°C",
            "special_requirements": "избегайте холодных сквозняков"
        },
        "humidity": {
            "optimal": "высокая",
            "methods": ["регулярное опрыскивание", "увлажнитель воздуха", "поддон с влажной галькой"],
            "special_requirements": "в сухом воздухе края листьев могут коричневеть"
        },
        "pruning": "удаляйте пожелтевшие или поврежденные листья; направляйте рост с помощью опоры",
        "propagation": ["стеблевые черенки с узлами", "деление при пересадке"],
        "common_problems": [
            {
                "название": "Коричневые края листьев",
                "решение": "обычно из-за низкой влажности воздуха; увеличьте влажность"
            },
            {
                "название": "Желтые листья",
                "решение": "чаще всего из-за переувлажнения; сократите полив и проверьте дренаж"
            },
            {
                "название": "Отсутствие разрезов на листьях",
                "решение": "растению может не хватать света; переместите в более светлое место"
            }
        ],
        "toxicity": {"для_людей": True, "для_животных": True},
        "seasonal_care": {
            "весна": "идеальное время для пересадки и увеличения полива",
            "лето": "период активного роста; регулярные подкормки и опрыскивание",
            "осень": "постепенно сокращайте полив и удобрение",
            "зима": "минимальный полив, без удобрений, защита от сквозняков"
        },
        "difficulty": "легкое",
        "tips": [
            "Используйте мох на опоре для поддержки воздушных корней",
            "Большие листья собирают пыль — регулярно протирайте их влажной тряпкой",
            "По мере роста растению понадобится опора или мох-столб для поддержки"
        ],
        "last_updated": datetime.now().isoformat()
    },
    {
        "name": "Суккуленты (общие рекомендации)",
        "scientific_name": "Различные виды",
        "category": "комнатное",
        "description": "Суккуленты — растения с мясистыми листьями, накапливающими влагу. Отличаются неприхотливостью и разнообразием форм.",
        "origin": "Различные регионы с засушливым климатом",
        "watering": {
            "frequency": "раз в 2-3 недели",
            "amount": "умеренно",
            "method": "полностью просушивайте почву между поливами",
            "seasonal_adjustments": {"зима": "сократите полив до 1 раза в месяц", "лето": "следите за почвой"}
        },
        "light": {
            "type": "яркое освещение",
            "hours": "6+ часов в день",
            "direction": "южное или западное окно",
            "additional_info": "большинство видов любят прямой солнечный свет, но некоторые могут требовать защиты в полдень"
        },
        "soil": {
            "type": "хорошо дренированная, песчаная",
            "ph": "нейтральная",
            "drainage": "превосходный дренаж обязателен",
            "composition": "специальная почвенная смесь для кактусов и суккулентов"
        },
        "fertilizer": {
            "frequency": "раз в 2-3 месяца в период роста",
            "type": "удобрение для кактусов и суккулентов",
            "strength": "половинная доза",
            "seasonal": "не удобряйте зимой",
            "special_needs": "избегайте удобрений с высоким содержанием азота"
        },
        "temperature": {
            "optimal": "18-27°C",
            "min": "большинство видов 5-10°C",
            "max": "не выше 40°C",
            "special_requirements": "большинство суккулентов переносят высокие температуры, но некоторые чувствительны к заморозкам"
        },
        "humidity": {
            "optimal": "низкая",
            "methods": ["хорошая вентиляция", "обеспечение сухого воздуха"],
            "special_requirements": "избегайте чрезмерной влажности, которая может вызвать гниение"
        },
        "pruning": "обычно не требуется; удаляйте отмершие листья",
        "propagation": ["листовые черенки", "отводки", "семена"],
        "common_problems": [
            {
                "название": "Вытягивание побегов",
                "решение": "недостаток света; переместите растение в более солнечное место"
            },
            {
                "название": "Гниение стебля или корней",
                "решение": "чрезмерный полив; дайте растению полностью высохнуть и сократите полив"
            },
            {
                "название": "Сморщивание листьев",
                "решение": "недостаток влаги; увеличьте частоту полива"
            }
        ],
        "toxicity": {"для_людей": False, "для_животных": False},
        "seasonal_care": {
            "весна": "постепенно увеличивайте полив после зимнего покоя",
            "лето": "регулярный полив, защита от экстремальной жары",
            "осень": "подготовка к периоду покоя, сокращение полива",
            "зима": "минимальный полив, сохранение сухости, яркий свет"
        },
        "difficulty": "легкое",
        "tips": [
            "Лучше недолить, чем перелить",
            "Используйте терракотовые горшки, которые позволяют почве быстрее просыхать",
            "Большинство суккулентов входят в период покоя зимой, когда их рост замедляется"
        ],
        "last_updated": datetime.now().isoformat()
    },
    {
        "name": "Хлорофитум",
        "scientific_name": "Chlorophytum comosum",
        "category": "комнатное",
        "description": "Неприхотливое комнатное растение с длинными узкими листьями, часто пестрыми. Также известен как «паучья лилия».",
        "origin": "Южная Африка",
        "watering": {
            "frequency": "раз в 7-10 дней",
            "amount": "умеренно",
            "method": "поддерживайте почву слегка влажной, но не мокрой",
            "seasonal_adjustments": {"зима": "сократите полив", "лето": "следите за почвой"}
        },
        "light": {
            "type": "яркий непрямой свет",
            "hours": "6+ часов в день",
            "direction": "подходит любое окно",
            "additional_info": "пестролистные сорта нуждаются в большем количестве света для сохранения окраски"
        },
        "soil": {
            "type": "легкая, хорошо дренированная",
            "ph": "нейтральная",
            "drainage": "хороший дренаж",
            "composition": "универсальный грунт с добавлением перлита"
        },
        "fertilizer": {
            "frequency": "раз в месяц с весны до осени",
            "type": "универсальное удобрение для комнатных растений",
            "strength": "по инструкции",
            "seasonal": "не удобряйте зимой",
            "special_needs": ""
        },
        "temperature": {
            "optimal": "18-24°C",
            "min": "не ниже 10°C",
            "max": "не выше 30°C",
            "special_requirements": "переносит широкий диапазон температур"
        },
        "humidity": {
            "optimal": "средняя",
            "methods": ["опрыскивание", "влажный воздух"],
            "special_requirements": "нормально чувствует себя в условиях обычной комнатной влажности"
        },
        "pruning": "удаляйте пожелтевшие или поврежденные листья; можно удалять столоны (детки) или оставлять для размножения",
        "propagation": ["разделение кустов", "столоны (молодые растения на концах длинных побегов)"],
        "common_problems": [
            {
                "название": "Коричневые кончики листьев",
                "решение": "низкая влажность воздуха или недостаток воды; увеличьте влажность или полив"
            },
            {
                "название": "Бледные листья",
                "решение": "недостаток света у пестролистных сортов; переместите в более светлое место"
            },
            {
                "название": "Отсутствие роста",
                "решение": "возможно, растению нужно удобрение или пересадка в больший горшок"
            }
        ],
        "toxicity": {"для_людей": False, "для_животных": False},
        "seasonal_care": {
            "весна": "хорошее время для деления и пересадки",
            "лето": "регулярный полив и подкормки, период активного роста",
            "осень": "сокращение полива и удобрений",
            "зима": "минимальный полив, без удобрений"
        },
        "difficulty": "очень легкое",
        "tips": [
            "Отлично очищает воздух от формальдегида и других загрязнителей",
            "Хорошо растет в подвесных кашпо, где могут свободно свисать детки",
            "Можно выращивать в воде"
        ],
        "last_updated": datetime.now().isoformat()
    }
]

class PlantCareTipsManager:
    """Class for managing plant care tips database"""
    
    def __init__(self):
        self.care_tips = []
        self.load_care_tips()
    
    def load_care_tips(self):
        """Load care tips from JSON file or initialize with defaults"""
        try:
            if os.path.exists(CARE_TIPS_PATH):
                with open(CARE_TIPS_PATH, 'r', encoding='utf-8') as f:
                    self.care_tips = json.load(f)
                    logger.info(f"Loaded {len(self.care_tips)} plant care tips from {CARE_TIPS_PATH}")
            else:
                self.care_tips = INITIAL_PLANT_CARE_TIPS
                self.save_care_tips()
                logger.info(f"Initialized plant care tips database with {len(self.care_tips)} default entries")
        except Exception as e:
            logger.error(f"Error loading plant care tips: {e}")
            self.care_tips = INITIAL_PLANT_CARE_TIPS
            logger.info("Using default plant care tips due to loading error")
    
    def save_care_tips(self):
        """Save care tips to JSON file"""
        try:
            with open(CARE_TIPS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.care_tips, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.care_tips)} plant care tips to {CARE_TIPS_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving plant care tips: {e}")
            return False
    
    def get_all_tips(self) -> List[Dict]:
        """Get all plant care tips"""
        return self.care_tips
    
    def get_tip_by_name(self, name: str) -> Optional[Dict]:
        """Get plant care tip by name"""
        for tip in self.care_tips:
            if tip["name"].lower() == name.lower():
                return tip
        
        # Try partial match
        for tip in self.care_tips:
            if name.lower() in tip["name"].lower():
                return tip
        
        return None
    
    def search_tips(self, query: str) -> List[Dict]:
        """Search plant care tips by query"""
        query = query.lower()
        results = []
        
        for tip in self.care_tips:
            if (query in tip["name"].lower() or 
                query in tip["scientific_name"].lower() or 
                query in tip["description"].lower()):
                results.append(tip)
        
        return results
    
    def add_tip(self, tip_data: Dict) -> bool:
        """Add new plant care tip"""
        # Check if plant already exists
        existing_tip = self.get_tip_by_name(tip_data["name"])
        if existing_tip:
            return False
        
        # Add timestamp
        tip_data["last_updated"] = datetime.now().isoformat()
        
        # Add to tips list
        self.care_tips.append(tip_data)
        
        # Save to file
        return self.save_care_tips()
    
    def update_tip(self, name: str, updated_data: Dict) -> bool:
        """Update existing plant care tip"""
        for i, tip in enumerate(self.care_tips):
            if tip["name"].lower() == name.lower():
                # Update timestamp
                updated_data["last_updated"] = datetime.now().isoformat()
                
                # Update tip
                self.care_tips[i] = {**tip, **updated_data}
                
                # Save to file
                return self.save_care_tips()
        
        return False
    
    def delete_tip(self, name: str) -> bool:
        """Delete plant care tip by name"""
        for i, tip in enumerate(self.care_tips):
            if tip["name"].lower() == name.lower():
                self.care_tips.pop(i)
                return self.save_care_tips()
        
        return False
    
    def format_care_tip(self, tip: Dict, detailed: bool = True) -> str:
        """Format plant care tip for display"""
        if not tip:
            return "Информация не найдена"
        
        if not detailed:
            return f"*{tip['name']}* (*{tip['scientific_name']}*): {tip['description']}"
        
        text = f"*{tip['name']}* (*{tip['scientific_name']}*)\n\n"
        text += f"{tip['description']}\n\n"
        
        text += "*Полив:*\n"
        text += f"• Частота: {tip['watering']['frequency']}\n"
        text += f"• Метод: {tip['watering']['method']}\n"
        if tip['watering']['seasonal_adjustments']:
            text += "• Сезонные корректировки: "
            for season, adj in tip['watering']['seasonal_adjustments'].items():
                text += f"{season} - {adj}; "
            text = text.rstrip("; ") + "\n"
        
        text += "\n*Освещение:*\n"
        text += f"• Тип: {tip['light']['type']}\n"
        text += f"• Длительность: {tip['light']['hours']}\n"
        if tip['light']['additional_info']:
            text += f"• Дополнительно: {tip['light']['additional_info']}\n"
        
        text += "\n*Почва:*\n"
        text += f"• Тип: {tip['soil']['type']}\n"
        text += f"• pH: {tip['soil']['ph']}\n"
        text += f"• Дренаж: {tip['soil']['drainage']}\n"
        
        text += "\n*Температура:*\n"
        text += f"• Оптимальная: {tip['temperature']['optimal']}\n"
        text += f"• Мин.: {tip['temperature']['min']}\n"
        text += f"• Макс.: {tip['temperature']['max']}\n"
        
        text += "\n*Влажность:*\n"
        text += f"• Оптимальная: {tip['humidity']['optimal']}\n"
        text += "• Методы поддержания: " + ", ".join(tip['humidity']['methods']) + "\n"
        
        if tip['common_problems']:
            text += "\n*Распространенные проблемы:*\n"
            for problem in tip['common_problems']:
                text += f"• *{problem['название']}*: {problem['решение']}\n"
        
        if tip['tips']:
            text += "\n*Полезные советы:*\n"
            for tip_item in tip['tips']:
                text += f"• {tip_item}\n"
        
        text += f"\n*Сложность ухода:* {tip['difficulty']}"
        
        return text

    def generate_care_instructions(self, plant_name: str) -> Optional[Dict]:
        """Generate structured care instructions for a plant"""
        tip = self.get_tip_by_name(plant_name)
        if not tip:
            return None
        
        # Create structured care instructions
        instructions = {
            "name": tip["name"],
            "scientific_name": tip["scientific_name"],
            "care_summary": f"Уровень сложности: {tip['difficulty']}",
            "watering": f"Поливайте {tip['watering']['frequency']}, {tip['watering']['method']}.",
            "light": f"Требуется {tip['light']['type']} {tip['light']['hours']}.",
            "temperature": f"Оптимальная температура {tip['temperature']['optimal']}.",
            "soil": f"{tip['soil']['type']} почва с {tip['soil']['drainage']}.",
            "humidity": f"{tip['humidity']['optimal']} влажность.",
            "fertilizing": tip.get("fertilizer", {}).get("frequency", "По необходимости"),
            "common_problems": [p["название"] for p in tip["common_problems"]],
            "tips": tip["tips"]
        }
        
        return instructions
    
    def get_seasonal_care(self, plant_name: str, season: str) -> Optional[str]:
        """Get seasonal care advice for a plant"""
        tip = self.get_tip_by_name(plant_name)
        if not tip or "seasonal_care" not in tip:
            return None
        
        season = season.lower()
        if season in tip["seasonal_care"]:
            return tip["seasonal_care"][season]
        
        return None


# Initialize the manager
plant_care_manager = PlantCareTipsManager()

# Add to global scope for easy access
def get_plant_care_manager():
    """Get the plant care tips manager instance"""
    return plant_care_manager

def get_tip_by_name(name: str) -> Optional[Dict]:
    """Get plant care tip by name"""
    return plant_care_manager.get_tip_by_name(name)

def search_tips(query: str) -> List[Dict]:
    """Search plant care tips by query"""
    return plant_care_manager.search_tips(query)

def format_care_tip(tip: Dict, detailed: bool = True) -> str:
    """Format plant care tip for display"""
    return plant_care_manager.format_care_tip(tip, detailed)

def generate_care_instructions(plant_name: str) -> Optional[Dict]:
    """Generate structured care instructions for a plant"""
    return plant_care_manager.generate_care_instructions(plant_name)

# If this file is run directly, initialize the database
if __name__ == "__main__":
    print(f"Loaded {len(plant_care_manager.get_all_tips())} plant care tips")
    print("Sample tip:")
    sample_tip = plant_care_manager.get_all_tips()[0]
    print(plant_care_manager.format_care_tip(sample_tip, detailed=False))
    print("\nDetailed format:")
    print(plant_care_manager.format_care_tip(sample_tip)) 