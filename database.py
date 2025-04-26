import os
import logging
import traceback
import motor.motor_asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson.objectid import ObjectId

from config import MONGO_URI, DB_NAME, PLANTS_COLLECTION, USERS_COLLECTION, FEEDBACK_COLLECTION

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, mongo_uri=None, db_name=None):
        self.mongo_uri = mongo_uri or MONGO_URI
        self.db_name = db_name or DB_NAME
        
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.plants = self.db[PLANTS_COLLECTION]
            self.users = self.db[USERS_COLLECTION]
            self.feedback = self.db[FEEDBACK_COLLECTION]
            logger.info(f"Connected to database: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def add_plant(self, plant_data: Dict[str, Any]) -> str:
        try:
            result = await self.plants.insert_one(plant_data)
            logger.info(f"Added plant: {plant_data.get('name', 'unknown')}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding plant: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def get_plant(self, plant_id: str) -> Dict[str, Any]:
        try:
            plant = await self.plants.find_one({"_id": ObjectId(plant_id)})
            return plant
        except Exception as e:
            logger.error(f"Error getting plant {plant_id}: {e}")
            return None
    
    def get_plant_by_name(self, name: str) -> Dict[str, Any]:
        try:
            return self.plants.find_one({"name": name})
        except Exception as e:
            logger.error(f"Error getting plant by name {name}: {e}")
            return None
    
    async def update_plant(self, plant_id, data: Dict[str, Any]) -> bool:
        try:
            result = await self.plants.update_one(
                {"_id": ObjectId(plant_id)},
                {"$set": data}
            )
            logger.info(f"Updated plant {plant_id}: {result.modified_count} document(s) modified")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating plant {plant_id}: {e}")
            return False
    
    async def delete_plant(self, plant_id: str) -> bool:
        try:
            result = await self.plants.delete_one({"_id": ObjectId(plant_id)})
            logger.info(f"Deleted plant {plant_id}: {result.deleted_count} document(s) deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting plant {plant_id}: {e}")
            return False
    
    async def search_plants(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            cursor = self.plants.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error searching plants with query '{query}': {e}")
            return []
    
    async def get_all_plants(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            cursor = self.plants.find().limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting all plants: {e}")
            return []
    
    async def add_user(self, user_data: Dict[str, Any]) -> str:
        try:
            user_data["created_at"] = datetime.utcnow()
            user_data["last_active"] = datetime.utcnow()
            
            existing_user = await self.users.find_one({"user_id": user_data["user_id"]})
            
            if existing_user:
                await self.users.update_one(
                    {"user_id": user_data["user_id"]},
                    {"$set": {
                        "last_active": datetime.utcnow(),
                        "username": user_data.get("username"),
                        "first_name": user_data.get("first_name"),
                        "last_name": user_data.get("last_name")
                    }}
                )
                return str(existing_user["_id"])
            
            result = await self.users.insert_one(user_data)
            logger.info(f"Added user: {user_data.get('username', user_data.get('user_id'))}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        try:
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        try:
            data["last_active"] = datetime.utcnow()
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    async def add_user_interaction(self, user_id: int, interaction_type: str, data: Dict[str, Any] = None) -> bool:
        try:
            if data is None:
                data = {}
                
            interaction = {
                "type": interaction_type,
                "timestamp": datetime.utcnow(),
                **data
            }
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$push": {"interactions": interaction},
                    "$set": {"last_active": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding interaction for user {user_id}: {e}")
            return False
    
    async def add_user_session(self, user_id: int, session_data: Dict[str, Any] = None) -> str:
        try:
            if session_data is None:
                session_data = {}
                
            session = {
                "started_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "session_id": str(ObjectId()),
                **session_data
            }
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$push": {"sessions": session},
                    "$set": {"current_session": session["session_id"], "last_active": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                return session["session_id"]
            
            return None
        except Exception as e:
            logger.error(f"Error adding session for user {user_id}: {e}")
            return None
    
    async def update_user_session(self, user_id: int, session_id: str, data: Dict[str, Any]) -> bool:
        try:
            data["last_activity"] = datetime.utcnow()
            
            result = await self.users.update_one(
                {"user_id": user_id, "sessions.session_id": session_id},
                {
                    "$set": {
                        "sessions.$.last_activity": datetime.utcnow(),
                        **{f"sessions.$.{k}": v for k, v in data.items()},
                        "last_active": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating session {session_id} for user {user_id}: {e}")
            return False
    
    async def add_feedback(self, feedback_data: Dict[str, Any]) -> str:
        try:
            feedback_data["created_at"] = datetime.utcnow()
            
            result = await self.feedback.insert_one(feedback_data)
            logger.info(f"Added feedback from user: {feedback_data.get('user_id', 'unknown')}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return None
    
    async def get_all_feedback(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            cursor = self.feedback.find().sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting all feedback: {e}")
            return []
            
    async def get_user_feedback(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            cursor = self.feedback.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting feedback for user {user_id}: {e}")
            return []
    
    async def create_indexes(self):
        try:
            await self.plants.create_index([("name", "text"), ("scientific_name", "text"), ("description", "text")])
            await self.users.create_index("user_id", unique=True)
            await self.feedback.create_index([("user_id", 1), ("created_at", -1)])
            
            logger.info("Created database indexes")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False
    
    async def get_plant_suggestions(self, partial_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            regex = f".*{partial_name}.*"
            cursor = self.plants.find({"name": {"$regex": regex, "$options": "i"}}).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting plant suggestions for '{partial_name}': {e}")
            return [] 