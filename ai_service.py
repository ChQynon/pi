import os
import re
import json
import random
import base64
import aiohttp
import asyncio
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from config import CHUTES_API_TOKEN, YOUTUBE_API_KEY

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or CHUTES_API_TOKEN
        self.base_url = "https://api.chutes.ai/api/v1"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
    async def generate_response(self, prompt, model="gpt-4o", max_retries=3, temperature=0.7):
        try:
            async with aiohttp.ClientSession() as session:
                for attempt in range(max_retries):
                    try:
                        async with session.post(
                            f"{self.base_url}/chat/completions",
                            headers=self.headers,
                            json={
                                "model": model,
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": temperature
                            },
                            timeout=60
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data["choices"][0]["message"]["content"]
                            elif response.status == 429:
                                wait_time = min(2 ** attempt, 16)
                                logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry.")
                                await asyncio.sleep(wait_time)
                            else:
                                logger.error(f"API error: {response.status} - {await response.text()}")
                                error_text = await response.text()
                                if "quota" in error_text.lower():
                                    logger.critical("API quota exceeded")
                                    return "К сожалению, я не могу ответить на ваш вопрос. Лимит запросов к API превышен."
                                return f"Произошла ошибка при обработке запроса. Попробуйте позже."
                    except asyncio.TimeoutError:
                        logger.warning(f"Request timed out. Attempt {attempt+1}/{max_retries}")
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"Error during API call: {str(e)}")
                        await asyncio.sleep(2)
                
                return "Извините, сервис временно недоступен. Попробуйте позже."
        except Exception as e:
            logger.exception(f"Critical error in generate_response: {e}")
            return "Произошла критическая ошибка. Пожалуйста, попробуйте позже."

    async def generate_image_analysis(self, prompt, image_url):
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(image_url) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch image: {response.status}")
                            return "Не удалось загрузить изображение"
                        
                        image_data = await response.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        messages = [
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]}
                        ]
                        
                        async with session.post(
                            f"{self.base_url}/chat/completions",
                            headers=self.headers,
                            json={
                                "model": "gpt-4o",
                                "messages": messages,
                                "temperature": 0.2
                            },
                            timeout=90
                        ) as ai_response:
                            if ai_response.status == 200:
                                data = await ai_response.json()
                                return data["choices"][0]["message"]["content"]
                            else:
                                logger.error(f"API error: {ai_response.status} - {await ai_response.text()}")
                                return "Произошла ошибка при анализе изображения"
                
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
                    return "Произошла ошибка при обработке изображения"
        
        except Exception as e:
            logger.exception(f"Critical error in analyze_image: {e}")
            return "Произошла критическая ошибка при анализе изображения"

    async def analyze_plant_image(self, image_url):
        try:
            prompt = (
                "Проанализируй изображение и определи, какое растение на нем изображено. "
                "Если растение не видно четко или невозможно определить, так и скажи. "
                "Если растение видно и можно определить, предоставь следующую информацию в структурированном виде:\n\n"
                "Название: [название растения на русском]\n"
                "Научное название: [латинское название]\n"
                "Описание: [краткое описание растения]\n"
                "Уход: [рекомендации по поливу, освещению, температуре]\n"
                "Распространенные проблемы: [список частых проблем]"
            )
            
            response = await self.generate_image_analysis(prompt, image_url)
            
            if "не могу определить" in response.lower() or "не видно" in response.lower():
                return {
                    "recognized": False,
                    "message": "Я не смог определить растение на этом изображении. Пожалуйста, сделайте более четкое фото при хорошем освещении."
                }
            
            return {
                "recognized": True,
                "analysis": response
            }
            
        except Exception as e:
            logger.exception(f"Error in analyze_plant_image: {e}")
            return {
                "recognized": False,
                "message": "Произошла ошибка при анализе изображения."
            }

    async def recognize_plant(self, image_url, db=None):
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
            
            response = await self.generate_image_analysis(prompt, image_url)
            
            try:
                json_match = re.search(r'({[\s\S]*})', response)
                if json_match:
                    json_str = json_match.group(1)
                    plant_data = json.loads(json_str)
                    
                    if not plant_data.get("name") or plant_data.get("name") == "Unknown":
                        return {
                            "recognized": False,
                            "message": "Я не смог определить растение на этом изображении. Пожалуйста, сделайте более четкое фото при хорошем освещении.",
                            "care_tips": "Без определения растения я не могу дать конкретные рекомендации по уходу."
                        }
                    
                    plant_data["last_updated"] = datetime.utcnow().isoformat()
                    plant_data["confidence"] = "high" if plant_data.get("scientific_name") else "medium"
                    
                    if db and plant_data.get("name"):
                        try:
                            existing_plant = await db.plants.find_one({"name": plant_data["name"]})
                            
                            if existing_plant:
                                await db.plants.update_one(
                                    {"name": plant_data["name"]},
                                    {"$set": plant_data}
                                )
                                logging.info(f"Updated plant data for '{plant_data['name']}' in database")
                            else:
                                await db.plants.insert_one(plant_data)
                                logging.info(f"Added new plant '{plant_data['name']}' to database")
                        except Exception as db_error:
                            logging.error(f"Error saving plant data to database: {db_error}")
                    
                    plant_data["recognized"] = True
                    return plant_data
                else:
                    name_match = re.search(r"Название:\s*(.+?)(?:\n|$)", response)
                    scientific_name_match = re.search(r"Научное название:\s*(.+?)(?:\n|$)", response)
                    
                    if not name_match or "не видно" in response.lower() or "невозможно определить" in response.lower():
                        return {
                            "recognized": False,
                            "message": "Я не смог определить растение на этом изображении. Пожалуйста, сделайте более четкое фото при хорошем освещении.",
                            "care_tips": "Без определения растения я не могу дать конкретные рекомендации по уходу."
                        }
                    
                    plant_name = name_match.group(1).strip() if name_match else "Неизвестное растение"
                    scientific_name = scientific_name_match.group(1).strip() if scientific_name_match else ""
                    
                    description_match = re.search(r"Описание:\s*(.+?)(?:\n|$)", response)
                    care_match = re.search(r"Уход:\s*(.+?)(?:\n|$)", response)
                    problems_match = re.search(r"Распространенные проблемы:\s*(.+?)(?:\n|$|Распространенные проблемы)", response)
                    
                    description = description_match.group(1).strip() if description_match else ""
                    care_tips = care_match.group(1).strip() if care_match else ""
                    problems = problems_match.group(1).strip() if problems_match else ""
                    
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

    async def identify_problem(self, description=None, image_url=None):
        try:
            if image_url:
                prompt = (
                    f"Проанализируй проблему с растением на изображении. "
                    "Определи возможные причины проблемы, опиши симптомы и предложи решения. "
                )
                
                if description:
                    prompt += f"Дополнительная информация от пользователя: {description}"
                
                response = await self.generate_image_analysis(prompt, image_url)
            else:
                if not description:
                    return "Пожалуйста, опишите проблему с растением или прикрепите фото."
                
                prompt = (
                    f"Пользователь описал проблему с растением: '{description}'. "
                    f"Определи возможные причины проблемы, основываясь на этом описании, "
                    f"и предложи подробные решения."
                )
                
                response = await self.generate_response(prompt)
            
            return response
            
        except Exception as e:
            logger.exception(f"Error in identify_problem: {e}")
            return "Произошла ошибка при анализе проблемы с растением."

    async def recommend_vitamins(self, query):
        try:
            prompt = (
                f"Пользователь спрашивает о витаминах: '{query}'. "
                f"Дай профессиональный ответ о витаминах, их пользе, источниках и рекомендациях по приему. "
                f"Если вопрос о дефиците или симптомах, объясни признаки недостатка и как его восполнить. "
                f"Ответь максимально информативно, но не более 2000 символов."
            )
            
            response = await self.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.exception(f"Error in recommend_vitamins: {e}")
            return "Произошла ошибка при обработке запроса о витаминах."

    async def general_question(self, query):
        try:
            prompt = (
                f"Вопрос пользователя: '{query}'. "
                f"Дай полезный и информативный ответ, основанный на фактах. "
                f"Если вопрос связан с растениями, садоводством или витаминами - дай особенно подробный ответ. "
                f"Если не знаешь точного ответа - так и скажи. "
                f"Ответ должен быть информативным, но не превышать 2000 символов."
            )
            
            response = await self.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.exception(f"Error in general_question: {e}")
            return "Произошла ошибка при обработке вашего вопроса."

    async def analyze_query_intent(self, query):
        try:
            prompt = (
                f"Определи, к какой категории относится следующий запрос пользователя: '{query}'. "
                f"Выбери одну из категорий: vitamin_info, vitamin_problem, plant_info, plant_problem, general_question. "
                f"Верни ТОЛЬКО название категории без дополнительного текста:"
            )
            
            response = await self.generate_response(prompt)
            
            intent = response.strip().lower()
            
            valid_intents = ["vitamin_info", "vitamin_problem", "plant_info", "plant_problem", "general_question"]
            if intent not in valid_intents:
                logger.warning(f"Invalid intent detected: {intent}, defaulting to general_question")
                intent = "general_question"
                
            logger.info(f"Query intent: {intent} for query: {query}")
            return intent
            
        except Exception as e:
            logger.exception(f"Error in analyze_query_intent: {e}")
            return "general_question"

    async def search_youtube_videos(self, query, max_results=5):
        try:
            if not YOUTUBE_API_KEY:
                logger.warning("YouTube API key not configured")
                return []
            
            youtube_query = f"{query} растения" if "растен" not in query.lower() else query
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'part': 'snippet',
                    'q': youtube_query,
                    'type': 'video',
                    'maxResults': max_results,
                    'key': YOUTUBE_API_KEY,
                    'relevanceLanguage': 'ru'
                }
                
                async with session.get('https://www.googleapis.com/youtube/v3/search', params=params) as response:
                    if response.status != 200:
                        logger.error(f"YouTube API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    videos = []
                    
                    for item in data.get('items', []):
                        if item['id']['kind'] == 'youtube#video':
                            video_id = item['id']['videoId']
                            title = item['snippet']['title']
                            thumbnail = item['snippet']['thumbnails']['medium']['url']
                            
                            videos.append({
                                'id': video_id,
                                'title': title,
                                'thumbnail': thumbnail,
                                'url': f'https://www.youtube.com/watch?v={video_id}'
                            })
                    
                    return videos
                    
        except Exception as e:
            logger.exception(f"Error in search_youtube_videos: {e}")
            return []
    
    async def save_plant_to_database(self, plant_info):
        try:
            from database import Database
            db = Database()
            
            existing_plant = db.get_plant_by_name(plant_info["name"])
            
            if existing_plant:
                plant_data = {
                    "name": plant_info["name"],
                    "scientific_name": plant_info["scientific_name"],
                }
                
                if plant_info.get("description") and plant_info["description"] not in ["Нет информации", ""]:
                    plant_data["description"] = plant_info["description"]
                
                if plant_info.get("care_tips") and plant_info["care_tips"] not in ["Нет информации", ""]:
                    plant_data["care_tips"] = plant_info["care_tips"]
                
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
                
                db.update_plant(existing_plant["_id"], plant_data)
                logger.info(f"Updated plant information: {plant_info['name']}")
            
            else:
                plant_data = {
                    "name": plant_info["name"],
                    "scientific_name": plant_info["scientific_name"],
                    "description": plant_info.get("description", ""),
                    "care_tips": plant_info.get("care_tips", ""),
                    "image_count": 1,
                    "last_updated": datetime.now().isoformat()
                }
                
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
                
                db.add_plant(plant_data)
                logger.info(f"Added new plant to database: {plant_info['name']}")
        
        except Exception as e:
            logger.exception(f"Error saving plant to database: {e}")