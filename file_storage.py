import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class FileStorage:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(os.path.join(self.data_dir, "plants"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "users"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "feedback"), exist_ok=True)
        
        # Индексные файлы
        self.plants_index_file = os.path.join(self.data_dir, "plants_index.json")
        self.users_index_file = os.path.join(self.data_dir, "users_index.json")
        
        # Создаем индексы если не существуют
        if not os.path.exists(self.plants_index_file):
            self._save_json(self.plants_index_file, {})
        if not os.path.exists(self.users_index_file):
            self._save_json(self.users_index_file, {})
    
    def _load_json(self, file_path):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path, data):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False
    
    async def add_plant(self, plant_data: Dict[str, Any]) -> str:
        try:
            plant_id = str(int(time.time() * 1000))
            plant_data["_id"] = plant_id
            plant_data["created_at"] = datetime.now().isoformat()
            
            # Сохраняем растение
            plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
            self._save_json(plant_file, plant_data)
            
            # Обновляем индекс
            plants_index = self._load_json(self.plants_index_file)
            plants_index[plant_id] = {"name": plant_data.get("name", ""), "id": plant_id}
            self._save_json(self.plants_index_file, plants_index)
            
            logger.info(f"Added plant: {plant_data.get('name', 'unknown')}")
            return plant_id
        except Exception as e:
            logger.error(f"Error adding plant: {e}")
            return None
    
    async def get_plant(self, plant_id: str) -> Dict[str, Any]:
        try:
            plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
            return self._load_json(plant_file)
        except Exception as e:
            logger.error(f"Error getting plant {plant_id}: {e}")
            return None
    
    def get_plant_by_name(self, name: str) -> Dict[str, Any]:
        try:
            plants_index = self._load_json(self.plants_index_file)
            for plant_id, info in plants_index.items():
                if info.get("name", "").lower() == name.lower():
                    plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
                    return self._load_json(plant_file)
            return None
        except Exception as e:
            logger.error(f"Error getting plant by name {name}: {e}")
            return None
    
    async def update_plant(self, plant_id, data: Dict[str, Any]) -> bool:
        try:
            plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
            if not os.path.exists(plant_file):
                return False
            
            plant_data = self._load_json(plant_file)
            plant_data.update(data)
            plant_data["updated_at"] = datetime.now().isoformat()
            
            self._save_json(plant_file, plant_data)
            logger.info(f"Updated plant {plant_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating plant {plant_id}: {e}")
            return False
    
    async def delete_plant(self, plant_id: str) -> bool:
        try:
            plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
            if not os.path.exists(plant_file):
                return False
            
            os.remove(plant_file)
            
            # Обновляем индекс
            plants_index = self._load_json(self.plants_index_file)
            if plant_id in plants_index:
                del plants_index[plant_id]
                self._save_json(self.plants_index_file, plants_index)
            
            logger.info(f"Deleted plant {plant_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting plant {plant_id}: {e}")
            return False
    
    async def search_plants(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            results = []
            plants_index = self._load_json(self.plants_index_file)
            
            for plant_id, info in plants_index.items():
                plant_name = info.get("name", "").lower()
                if query.lower() in plant_name:
                    plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
                    plant_data = self._load_json(plant_file)
                    results.append(plant_data)
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            logger.error(f"Error searching plants with query '{query}': {e}")
            return []
    
    async def get_all_plants(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            results = []
            plants_index = self._load_json(self.plants_index_file)
            
            count = 0
            for plant_id in plants_index:
                if count >= limit:
                    break
                    
                plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
                plant_data = self._load_json(plant_file)
                results.append(plant_data)
                count += 1
            
            return results
        except Exception as e:
            logger.error(f"Error getting all plants: {e}")
            return []
    
    async def add_user(self, user_data: Dict[str, Any]) -> str:
        try:
            user_id = str(user_data.get("user_id"))
            user_data["created_at"] = datetime.now().isoformat()
            user_data["last_active"] = datetime.now().isoformat()
            
            # Проверяем существует ли пользователь
            user_file = os.path.join(self.data_dir, "users", f"{user_id}.json")
            if os.path.exists(user_file):
                existing_user = self._load_json(user_file)
                existing_user["last_active"] = datetime.now().isoformat()
                existing_user["username"] = user_data.get("username")
                existing_user["first_name"] = user_data.get("first_name")
                existing_user["last_name"] = user_data.get("last_name")
                
                self._save_json(user_file, existing_user)
                return user_id
            
            # Сохраняем пользователя
            self._save_json(user_file, user_data)
            
            # Обновляем индекс
            users_index = self._load_json(self.users_index_file)
            users_index[user_id] = {"username": user_data.get("username", ""), "id": user_id}
            self._save_json(self.users_index_file, users_index)
            
            logger.info(f"Added user: {user_data.get('username', user_id)}")
            return user_id
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        try:
            user_file = os.path.join(self.data_dir, "users", f"{user_id}.json")
            return self._load_json(user_file)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        try:
            user_file = os.path.join(self.data_dir, "users", f"{user_id}.json")
            if not os.path.exists(user_file):
                return False
            
            user_data = self._load_json(user_file)
            data["last_active"] = datetime.now().isoformat()
            user_data.update(data)
            
            self._save_json(user_file, user_data)
            return True
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    async def add_user_interaction(self, user_id: int, interaction_type: str, data: Dict[str, Any] = None) -> bool:
        try:
            if data is None:
                data = {}
                
            user_file = os.path.join(self.data_dir, "users", f"{user_id}.json")
            if not os.path.exists(user_file):
                return False
            
            user_data = self._load_json(user_file)
            
            interaction = {
                "type": interaction_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
            
            if "interactions" not in user_data:
                user_data["interactions"] = []
                
            user_data["interactions"].append(interaction)
            user_data["last_active"] = datetime.now().isoformat()
            
            self._save_json(user_file, user_data)
            return True
        except Exception as e:
            logger.error(f"Error adding interaction for user {user_id}: {e}")
            return False
    
    async def add_feedback(self, feedback_data: Dict[str, Any]) -> str:
        try:
            feedback_id = str(int(time.time() * 1000))
            feedback_data["_id"] = feedback_id
            feedback_data["created_at"] = datetime.now().isoformat()
            
            # Сохраняем отзыв
            feedback_file = os.path.join(self.data_dir, "feedback", f"{feedback_id}.json")
            self._save_json(feedback_file, feedback_data)
            
            logger.info(f"Added feedback from user: {feedback_data.get('user_id', 'unknown')}")
            return feedback_id
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return None
    
    async def get_all_feedback(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            results = []
            feedback_dir = os.path.join(self.data_dir, "feedback")
            
            count = 0
            for filename in sorted(os.listdir(feedback_dir), reverse=True):
                if count >= limit:
                    break
                
                if filename.endswith(".json"):
                    feedback_file = os.path.join(feedback_dir, filename)
                    feedback_data = self._load_json(feedback_file)
                    results.append(feedback_data)
                    count += 1
            
            return results
        except Exception as e:
            logger.error(f"Error getting all feedback: {e}")
            return []
            
    async def get_user_feedback(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            results = []
            feedback_dir = os.path.join(self.data_dir, "feedback")
            
            count = 0
            for filename in sorted(os.listdir(feedback_dir), reverse=True):
                if count >= limit:
                    break
                    
                if filename.endswith(".json"):
                    feedback_file = os.path.join(feedback_dir, filename)
                    feedback_data = self._load_json(feedback_file)
                    
                    if str(feedback_data.get("user_id")) == str(user_id):
                        results.append(feedback_data)
                        count += 1
            
            return results
        except Exception as e:
            logger.error(f"Error getting feedback for user {user_id}: {e}")
            return []
    
    async def get_plant_suggestions(self, partial_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            results = []
            plants_index = self._load_json(self.plants_index_file)
            
            count = 0
            for plant_id, info in plants_index.items():
                if count >= limit:
                    break
                    
                plant_name = info.get("name", "").lower()
                if partial_name.lower() in plant_name:
                    plant_file = os.path.join(self.data_dir, "plants", f"{plant_id}.json")
                    plant_data = self._load_json(plant_file)
                    results.append(plant_data)
                    count += 1
            
            return results
        except Exception as e:
            logger.error(f"Error getting plant suggestions for '{partial_name}': {e}")
            return [] 