import aiohttp
import json
import os
import logging
from dotenv import load_dotenv
import re
from datetime import datetime
from plant_care_tips import get_plant_care_manager, generate_care_instructions

# Load environment variables
load_dotenv()

# Get API token from environment
API_TOKEN = os.getenv("OPENROUTER_API_KEY", "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")

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_token=None):
        self.api_token = api_token or API_TOKEN
        if not self.api_token:
            logger.warning("No OPENROUTER_API_KEY provided. AI features will not work.")
        
        # OpenRouter API settings
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openrouter/optimus-alpha"
        self.referer = "https://t.me/your_bot"
        self.site_name = "PLEXY Plant & Vitamin Bot"
    
    async def generate_response(self, prompt, max_tokens=1024, temperature=0.7):
        """Generate a response from the AI model"""
        if not self.api_token:
            return "Ошибка: API ключ не настроен. Обратитесь к администратору."
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.referer,
            "X-Title": self.site_name
        }
        
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=headers,
                    json=body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return "Произошла ошибка при обращении к AI. Попробуйте позже."
                    
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"Unexpected API response: {result}")
                        return "Получен неожиданный ответ от AI. Попробуйте позже."
        except Exception as e:
            logger.exception(f"Error calling AI API: {e}")
            return "Произошла ошибка при обращении к AI сервису. Попробуйте позже."
    
    async def analyze_plant_image(self, image_url):
        """Analyze a plant image and provide feedback"""
        prompt = f"""Проанализируй это растение по изображению:
        
        Определи:
        1. Предположительный вид растения
        2. Состояние здоровья растения (есть ли признаки болезней или проблем)
        3. Рекомендации по уходу
        4. Плюсы и минусы выращивания этого растения
        
        Формат ответа:
        **Растение**: [название, если возможно определить]
        **Состояние**: [оценка состояния]
        **Рекомендации по уходу**: [краткие рекомендации]
        **Плюсы**: [список преимуществ]
        **Минусы**: [список недостатков]
        """
        
        if not self.api_token:
            return "Ошибка: API ключ не настроен. Обратитесь к администратору."
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.referer,
            "X-Title": self.site_name
        }
        
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=headers,
                    json=body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return "Произошла ошибка при обращении к AI. Попробуйте позже."
                    
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"Unexpected API response: {result}")
                        return "Получен неожиданный ответ от AI. Попробуйте позже."
        except Exception as e:
            logger.exception(f"Error calling AI API for image analysis: {e}")
            return "Произошла ошибка при обращении к AI сервису. Попробуйте позже."
    
    async def recommend_vitamins(self, user_query):
        """Recommend vitamins based on user query"""
        prompt = f"""Пользователь спрашивает о витаминах: "{user_query}"
        
        Дай обоснованные рекомендации по витаминам или минералам, основываясь на запросе.
        
        Включи следующую информацию:
        1. Какие витамины и минералы рекомендуются в данной ситуации
        2. Рекомендуемые дозировки
        3. Натуральные источники этих витаминов в продуктах питания 
        4. Возможные противопоказания или предостережения
        5. Типичные проблемы, связанные с приемом данных витаминов и их решения
        
        Если запрос касается какого-то состояния здоровья, обязательно укажи, что необходима консультация врача.
        
        Формат ответа:
        **Рекомендуемые витамины и минералы**:
        [список с кратким описанием]
        
        **Дозировка**:
        [информация о дозировке]
        
        **Натуральные источники**:
        [список продуктов]
        
        **Предостережения**:
        [важные предостережения]
        
        **Типичные проблемы и решения**:
        [проблема 1] → [решение]
        [проблема 2] → [решение]
        
        **Важно**: [медицинский дисклеймер при необходимости]
        """
        
        return await self.generate_response(prompt, max_tokens=1800)
    
    async def recognize_plant(self, image_url, db=None):
        """
        Recognize a plant from an image URL and store the information in the database if provided.
        
        Args:
            image_url: URL of the image to analyze
            db: MongoDB database instance for storing plant data (optional)
            
        Returns:
            Dict containing plant information
        """
        try:
            prompt = (
                "Analyze the image and identify the plant shown. "
                "If the plant is not clearly visible or cannot be identified, say so. "
                "If the plant can be identified, provide the following information as a JSON object:\n\n"
                "{\n"
                "  \"name\": \"[plant name in Russian]\",\n"
                "  \"scientific_name\": \"[Latin name]\",\n"
                "  \"type\": \"[plant type: indoor, outdoor, etc.]\",\n"
                "  \"description\": \"[short description of the plant]\",\n"
                "  \"care_tips\": {\n"
                "    \"watering\": \"[watering instructions]\",\n"
                "    \"light\": \"[light requirements]\",\n"
                "    \"temperature\": \"[temperature requirements]\",\n"
                "    \"soil\": \"[soil requirements]\"\n"
                "  },\n"
                "  \"benefits\": \"[health or environmental benefits]\",\n"
                "  \"common_problems\": [\"[problem 1]\", \"[problem 2]\"]\n"
                "}\n\n"
                "Ensure the response is ONLY the JSON object, nothing else."
            )
            
            # Use the image analysis method
            response = await self.generate_image_analysis(prompt, image_url)
            
            # Try to extract JSON data from response
            try:
                # Find JSON pattern in the response
                json_match = re.search(r'({[\s\S]*})', response)
                if json_match:
                    json_str = json_match.group(1)
                    plant_data = json.loads(json_str)
                    
                    # Check if the plant was recognized
                    if not plant_data.get("name") or plant_data.get("name") == "Unknown":
                        return {
                            "recognized": False,
                            "message": "Я не смог определить растение на этом изображении. Пожалуйста, сделайте более четкое фото при хорошем освещении.",
                            "care_tips": "Без определения растения я не могу дать конкретные рекомендации по уходу."
                        }
                    
                    # Add timestamp and confidence
                    plant_data["last_updated"] = datetime.utcnow().isoformat()
                    plant_data["confidence"] = "high" if plant_data.get("scientific_name") else "medium"
                    
                    # Store plant information in database if provided
                    if db and plant_data.get("name"):
                        try:
                            # Check if plant already exists
                            existing_plant = await db.plants.find_one({"name": plant_data["name"]})
                            
                            if existing_plant:
                                # Update existing plant
                                await db.plants.update_one(
                                    {"name": plant_data["name"]},
                                    {"$set": plant_data}
                                )
                                logging.info(f"Updated plant data for '{plant_data['name']}' in database")
                            else:
                                # Create new plant entry
                                await db.plants.insert_one(plant_data)
                                logging.info(f"Added new plant '{plant_data['name']}' to database")
                        except Exception as db_error:
                            logging.error(f"Error saving plant data to database: {db_error}")
                    
                    # Add recognized flag for response
                    plant_data["recognized"] = True
                    return plant_data
                else:
                    # If JSON parsing failed, extract info using regex as fallback
                    name_match = re.search(r"Название:\s*(.+?)(?:\n|$)", response)
                    scientific_name_match = re.search(r"Научное название:\s*(.+?)(?:\n|$)", response)
                    
                    if not name_match or "не видно" in response.lower() or "невозможно определить" in response.lower():
                        return {
                            "recognized": False,
                            "message": "Я не смог определить растение на этом изображении. Пожалуйста, сделайте более четкое фото при хорошем освещении.",
                            "care_tips": "Без определения растения я не могу дать конкретные рекомендации по уходу."
                        }
                    
                    # Create basic plant data from regex matches
                    plant_name = name_match.group(1).strip() if name_match else "Неизвестное растение"
                    scientific_name = scientific_name_match.group(1).strip() if scientific_name_match else ""
                    
                    # Extract other information using regex
                    description_match = re.search(r"Описание:\s*(.+?)(?:\n|$)", response)
                    care_match = re.search(r"Уход:\s*(.+?)(?:\n|$)", response)
                    problems_match = re.search(r"Распространенные проблемы:\s*(.+?)(?:\n|$|Распространенные проблемы)", response)
                    
                    description = description_match.group(1).strip() if description_match else ""
                    care_tips = care_match.group(1).strip() if care_match else ""
                    problems = problems_match.group(1).strip() if problems_match else ""
                    
                    # Create plant data dictionary
                    fallback_data = {
                        "recognized": True,
                        "name": plant_name,
                        "scientific_name": scientific_name,
                        "description": description,
                        "care_tips": {"general": care_tips},
                        "common_problems": [problems] if problems else [],
                        "confidence": "medium" if scientific_name else "low",
                        "last_updated": datetime.utcnow().isoformat()
                    }
                    
                    return fallback_data
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse plant recognition response as JSON: {e}")
                return {
                    "recognized": False,
                    "message": "Произошла ошибка при обработке ответа о растении.",
                    "error": str(e)
                }
                
        except Exception as e:
            logging.error(f"Error in recognize_plant: {e}")
            return {
                "recognized": False,
                "message": "Произошла ошибка при распознавании растения.",
                "care_tips": "Попробуйте сделать более четкое фото при хорошем освещении."
            }
    
    async def get_generic_plant_tips(self, plant_name):
        """Get generic care tips for a plant based on its name"""
        if plant_name == "Неизвестное растение":
            return """
- Проверьте влажность почвы: если она сухая — полейте растение, но избегайте переувлажнения.
- Обрежьте все полностью засохшие и гнилые части.
- Пересмотрите условия освещения: возможно, растение нуждается в большем количестве света.
- Проверьте корни на наличие гнили — при необходимости пересадите растение в свежий грунт.
- При необходимости обработайте растение фунгицидом или инсектицидом.
- Дайте растению время на восстановление и следите за динамикой состояния.
"""
        else:
            # Try to get plant care tips from AI
            prompt = f"Дай краткие рекомендации по уходу за растением {plant_name}. Включи информацию о поливе, освещении, температуре и почве. Ответ должен быть не более 8-10 пунктов."
            try:
                tips = await self.generate_response(prompt, max_tokens=800, temperature=0.7)
                return tips
            except:
                # Fallback to generic tips
                return """
- Наблюдайте за растением и адаптируйте уход под его потребности.
- Поливайте умеренно, давая почве слегка просохнуть между поливами.
- Обеспечьте яркий рассеянный свет, избегая прямых солнечных лучей.
- Поддерживайте стабильную температуру 18-24°C.
- Регулярно осматривайте растение на наличие вредителей и заболеваний.
- Удаляйте пожелтевшие и засохшие листья.
- Подкармливайте растение в период активного роста.
"""

    async def save_plant_to_database(self, plant_info):
        """Save plant information to database for future reference
        
        Args:
            plant_info (dict): Plant information dictionary
        """
        try:
            from database import Database
            db = Database()
            
            # Check if plant already exists
            existing_plant = db.get_plant_by_name(plant_info["name"])
            
            if existing_plant:
                # Update existing entry with any new information
                plant_data = {
                    "name": plant_info["name"],
                    "scientific_name": plant_info["scientific_name"],
                }
                
                # Only update fields that have real information
                if plant_info.get("description") and plant_info["description"] not in ["Нет информации", ""]:
                    plant_data["description"] = plant_info["description"]
                
                if plant_info.get("care_tips") and plant_info["care_tips"] not in ["Нет информации", ""]:
                    plant_data["care_tips"] = plant_info["care_tips"]
                
                # Additional fields can be added to the database
                extra_data = {}
                if plant_info.get("light") and plant_info["light"] not in ["Нет информации", ""]:
                    extra_data["light"] = plant_info["light"]
                
                if plant_info.get("water") and plant_info["water"] not in ["Нет информации", ""]:
                    extra_data["watering"] = plant_info["water"]
                
                if plant_info.get("temperature") and plant_info["temperature"] not in ["Нет информации", ""]:
                    extra_data["temperature"] = plant_info["temperature"]
                
                if plant_info.get("soil") and plant_info["soil"] not in ["Нет информации", ""]:
                    extra_data["soil"] = plant_info["soil"]
                
                if plant_info.get("problems") and plant_info["problems"] not in ["Нет информации", ""]:
                    extra_data["common_problems"] = plant_info["problems"]
                
                if extra_data:
                    plant_data["extra_data"] = extra_data
                
                # Update plant in database
                db.update_plant(existing_plant["_id"], plant_data)
                logger.info(f"Updated plant information: {plant_info['name']}")
            
            else:
                # Create a new plant entry
                plant_data = {
                    "name": plant_info["name"],
                    "scientific_name": plant_info["scientific_name"],
                    "description": plant_info.get("description", ""),
                    "care_tips": plant_info.get("care_tips", ""),
                    "image_count": 1,
                    "last_updated": datetime.now().isoformat()
                }
                
                # Add extra data if available
                extra_data = {}
                if plant_info.get("light") and plant_info["light"] not in ["Нет информации", ""]:
                    extra_data["light"] = plant_info["light"]
                
                if plant_info.get("water") and plant_info["water"] not in ["Нет информации", ""]:
                    extra_data["watering"] = plant_info["water"]
                
                if plant_info.get("temperature") and plant_info["temperature"] not in ["Нет информации", ""]:
                    extra_data["temperature"] = plant_info["temperature"]
                
                if plant_info.get("soil") and plant_info["soil"] not in ["Нет информации", ""]:
                    extra_data["soil"] = plant_info["soil"]
                
                if plant_info.get("problems") and plant_info["problems"] not in ["Нет информации", ""]:
                    extra_data["common_problems"] = plant_info["problems"]
                
                if extra_data:
                    plant_data["extra_data"] = extra_data
                
                # Add plant to database
                db.add_plant(plant_data)
                logger.info(f"Added new plant to database: {plant_info['name']}")
        
        except Exception as e:
            logger.exception(f"Error saving plant to database: {e}")
            # Don't raise the exception - this is a non-critical operation
    
    async def get_ai_response(self, query):
        """Generate a concise AI response to a general query"""
        prompt = f"""Ответь на вопрос пользователя кратко и по существу:
        "{query}"
        
        Правила:
        1. Давай только точную и проверенную информацию
        2. Ответ должен быть кратким (не более 3-5 предложений)
        3. Используй простой язык без сложных терминов
        4. Если это вопрос о здоровье, добавь напоминание о консультации со специалистом
        5. НЕ используй разметку типа **, ## и подобные символы - используй только обычный текст
        
        Пример формата ответа:
        PLEXY: Витамин C помогает укрепить иммунитет. Его много в цитрусовых, киви и болгарском перце. Суточная норма - 75-90 мг.
        """
        
        response = await self.generate_response(prompt, max_tokens=800, temperature=0.7)
        
        # Remove any markdown symbols
        response = response.replace("**", "").replace("##", "").replace("*", "")
        
        # Ensure response starts with PLEXY
        if not response.startswith("PLEXY:"):
            response = f"PLEXY: {response}"
            
        return response
    
    async def identify_problem(self, description, problem_type="general"):
        """Identify a problem and suggest solutions based on description"""
        problem_prompts = {
            "vitamin": f"""Пользователь описывает следующую проблему, связанную с витаминами или минералами:
            "{description}"
            
            Пожалуйста:
            1. Определи, о какой проблеме идет речь
            2. Предложи возможные причины этой проблемы
            3. Порекомендуй конкретные решения и действия
            4. Укажи, какие витамины или минералы могут помочь в данной ситуации
            
            Формат ответа:
            **Проблема**: [краткое описание идентифицированной проблемы]
            
            **Возможные причины**:
            - [причина 1]
            - [причина 2]
            - ...
            
            **Рекомендуемые решения**:
            1. [решение 1]
            2. [решение 2]
            3. ...
            
            **Полезные витамины/минералы**:
            - [витамин/минерал 1]: [краткое пояснение]
            - [витамин/минерал 2]: [краткое пояснение]
            
            **Важно**: [медицинский дисклеймер при необходимости]
            """,
            
            "plant": f"""Пользователь описывает следующую проблему, связанную с комнатными растениями:
            "{description}"
            
            Пожалуйста:
            1. Определи, о какой проблеме идет речь
            2. Предложи возможные причины этой проблемы
            3. Порекомендуй решения с использованием бытовых отходов (если применимо)
            4. Дай дополнительные рекомендации по уходу
            
            Формат ответа:
            **Проблема**: [краткое описание идентифицированной проблемы]
            
            **Возможные причины**:
            - [причина 1]
            - [причина 2]
            - ...
            
            **Решения с использованием бытовых отходов**:
            1. [решение 1 с указанием типа отходов]
            2. [решение 2 с указанием типа отходов]
            3. ...
            
            **Дополнительные рекомендации**:
            - [рекомендация 1]
            - [рекомендация 2]
            """,
            
            "general": f"""Пользователь задал следующий вопрос или описал проблему:
            "{description}"
            
            Пожалуйста:
            1. Определи, о чем идет речь (витамины, растения или что-то другое)
            2. Дай развернутый и информативный ответ
            3. Предложи конкретные рекомендации или решения
            
            Формат ответа:
            **Ответ**: [основной ответ на вопрос]
            
            **Рекомендации**:
            - [рекомендация 1]
            - [рекомендация 2]
            - ...
            
            **Дополнительная информация**: [любая уместная дополнительная информация]
            """
        }
        
        prompt = problem_prompts.get(problem_type, problem_prompts["general"])
        return await self.generate_response(prompt, max_tokens=1800)
    
    async def analyze_query_intent(self, query):
        """Analyze the intent of the user's query."""
        prompt = (
            f"Определи тип запроса пользователя. Ответь только одним словом из следующих категорий: \n"
            f"vitamin_info - если пользователь спрашивает информацию о витаминах или добавках\n"
            f"vitamin_problem - если пользователь описывает проблему или симптом, связанный с дефицитом витаминов\n"
            f"plant_info - если пользователь спрашивает информацию о растении\n"
            f"plant_problem - если пользователь описывает проблему с растением\n"
            f"general_question - для любых других вопросов\n\n"
            f"Запрос пользователя: {query}"
        )
        
        response = await self.generate_response(prompt, max_tokens=100)
        return response.strip().lower()
        
    async def generate_image_analysis(self, prompt, image_url, max_tokens=1000, model=None):
        """
        Generate a response to a prompt with an image using the OpenRouter API.
        
        Args:
            prompt: Text prompt to send to the API
            image_url: URL of the image to analyze
            max_tokens: Maximum number of tokens to generate
            model: Model to use (defaults to self.model)
            
        Returns:
            String response from the API
        """
        if not model:
            model = self.model
            
        try:
            # Send request to OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.referer,
                "X-Title": self.site_name
            }
            
            body = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=headers,
                    json=body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(f"API error: {response.status} - {error_text}")
                        raise Exception(f"API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        logging.error(f"Unexpected API response: {result}")
                        raise Exception("Unexpected API response format")
                        
        except Exception as e:
            logging.error(f"Error in generate_image_analysis: {e}")
            raise

    async def get_plant_care_tips(self, plant_name):
        """Get detailed care tips for a specific plant
        
        Args:
            plant_name (str): Name of the plant to get care tips for
            
        Returns:
            dict: Structured care tips or error message
        """
        # Try to get information from our database first
        plant_care_manager = get_plant_care_manager()
        care_instructions = generate_care_instructions(plant_name)
        
        if care_instructions:
            logging.info(f"Found plant care tips in database for: {plant_name}")
            return {
                "found": True,
                "name": care_instructions["name"],
                "care_tips": {
                    "watering": care_instructions["watering"],
                    "light": care_instructions["light"],
                    "temperature": care_instructions["temperature"],
                    "soil": care_instructions["soil"],
                    "humidity": care_instructions.get("humidity", ""),
                    "fertilizing": care_instructions.get("fertilizing", "")
                },
                "common_problems": care_instructions.get("common_problems", []),
                "tips": care_instructions.get("tips", []),
                "source": "database"
            }
        
        # If not found in database, try to get from AI
        logging.info(f"Plant not found in database, attempting AI generation for: {plant_name}")
        try:
            prompt = f"""
Предоставь подробную информацию по уходу за растением "{plant_name}".
Сформируй ответ в виде JSON со следующими ключами:
{{
  "name": "{plant_name}",
  "watering": "подробно о поливе",
  "light": "требования к освещению",
  "temperature": "оптимальная температура",
  "soil": "требования к почве",
  "humidity": "требования к влажности",
  "fertilizing": "рекомендации по удобрению",
  "common_problems": ["проблема 1", "проблема 2"],
  "tips": ["совет 1", "совет 2", "совет 3"]
}}
ВАЖНО: Ответь только в формате JSON, без дополнительного текста.
"""
            response = await self.generate_response(prompt)
            
            # Try to extract JSON from response
            try:
                json_match = re.search(r'({[\s\S]*})', response)
                if json_match:
                    care_data = json.loads(json_match.group(1))
                    
                    # Store this in our database for future use
                    try:
                        new_tip = {
                            "name": care_data["name"],
                            "scientific_name": care_data.get("scientific_name", ""),
                            "category": "комнатное",
                            "description": care_data.get("description", ""),
                            "watering": {
                                "frequency": care_data.get("watering", "").split(",")[0] if "," in care_data.get("watering", "") else care_data.get("watering", ""),
                                "amount": "умеренно",
                                "method": care_data.get("watering", "").split(",")[1] if "," in care_data.get("watering", "") else "",
                                "seasonal_adjustments": {}
                            },
                            "light": {
                                "type": care_data.get("light", ""),
                                "hours": "",
                                "direction": "",
                                "additional_info": ""
                            },
                            "soil": {
                                "type": care_data.get("soil", ""),
                                "ph": "",
                                "drainage": "",
                                "composition": ""
                            },
                            "temperature": {
                                "optimal": care_data.get("temperature", ""),
                                "min": "",
                                "max": "",
                                "special_requirements": ""
                            },
                            "humidity": {
                                "optimal": care_data.get("humidity", ""),
                                "methods": [],
                                "special_requirements": ""
                            },
                            "common_problems": [{"название": problem, "решение": ""} for problem in care_data.get("common_problems", [])],
                            "tips": care_data.get("tips", []),
                            "difficulty": "среднее"
                        }
                        
                        plant_care_manager.add_tip(new_tip)
                        logging.info(f"Added new plant care tip to database: {care_data['name']}")
                    except Exception as db_error:
                        logging.error(f"Error saving new plant care tip to database: {db_error}")
                    
                    return {
                        "found": True,
                        "name": care_data["name"],
                        "care_tips": {
                            "watering": care_data.get("watering", ""),
                            "light": care_data.get("light", ""),
                            "temperature": care_data.get("temperature", ""),
                            "soil": care_data.get("soil", ""),
                            "humidity": care_data.get("humidity", ""),
                            "fertilizing": care_data.get("fertilizing", "")
                        },
                        "common_problems": care_data.get("common_problems", []),
                        "tips": care_data.get("tips", []),
                        "source": "ai"
                    }
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error parsing AI response for plant care: {e}")
        
        except Exception as e:
            logging.error(f"Error getting plant care tips from AI: {e}")
        
        # If all else fails, return generic tips
        return {
            "found": False,
            "name": plant_name,
            "message": f"Я не смог найти информацию о растении '{plant_name}'. Вот общие рекомендации по уходу за растениями:",
            "generic_tips": [
                "Проверяйте влажность почвы перед поливом. Большинство растений не любят переувлажнение.",
                "Обеспечьте подходящее освещение. Большинство комнатных растений предпочитают яркий непрямой свет.",
                "Поддерживайте оптимальную температуру 18-24°C для большинства комнатных растений.",
                "Используйте подходящую почву с хорошим дренажем.",
                "Регулярно осматривайте растение на наличие вредителей и болезней."
            ]
        }