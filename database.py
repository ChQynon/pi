from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from config import MONGO_URI, DB_NAME, VITAMINS_COLLECTION, PLANTS_COLLECTION, USERS_COLLECTION, FEEDBACK_COLLECTION
from datetime import datetime

# Sample data for when DB is not available
SAMPLE_VITAMINS = [
    {
        "name": "Витамин C",
        "short_description": "Антиоксидант, важен для иммунитета",
        "description": "Витамин C (аскорбиновая кислота) - мощный антиоксидант, необходимый для роста и восстановления тканей организма.",
        "benefits": "Укрепляет иммунитет\nУскоряет заживление ран\nУлучшает усвоение железа",
        "sources": "Цитрусовые\nКиви\nШиповник\nСладкий перец\nБрокколи",
        "deficiency": "Частые простуды\nМедленное заживление ран\nКровоточивость десен",
        "overdose": "Расстройство желудка\nДиарея\nВздутие живота",
        "daily_intake": "75-90 мг для взрослых"
    },
    {
        "name": "Витамин D",
        "short_description": "Важен для костей и иммунитета",
        "description": "Витамин D регулирует усвоение кальция и фосфора, необходим для здоровья костей и иммунной системы.",
        "benefits": "Укрепляет кости\nПоддерживает иммунитет\nРегулирует настроение",
        "sources": "Жирная рыба\nЯичные желтки\nПеченка\nГрибы\nСинтезируется в коже под действием солнечных лучей",
        "deficiency": "Рахит у детей\nОстеопороз\nМышечная слабость",
        "overdose": "Тошнота\nРвота\nСлабость\nПочечные проблемы",
        "daily_intake": "600-800 МЕ для взрослых"
    }
]

SAMPLE_PLANTS = [
    {
        "waste_type": "Кофейная гуща",
        "short_description": "Органическое удобрение для комнатных растений",
        "description": "Кофейная гуща - отличное органическое удобрение, богатое азотом, фосфором и калием.",
        "benefits": "Обогащает почву азотом\nОтпугивает вредителей\nУлучшает дренаж",
        "application": "Высушить гущу\nСмешать с почвой (1:4)\nИспользовать как мульчу",
        "suitable_plants": "Розы\nАзалии\nКамелии\nПапоротники\nЦитрусовые",
        "precautions": "Не использовать для растений, предпочитающих щелочную почву\nНе перебарщивать - может закислить почву"
    },
    {
        "waste_type": "Яичная скорлупа",
        "short_description": "Натуральный источник кальция для растений",
        "description": "Яичная скорлупа богата кальцием и другими микроэлементами, полезными для растений.",
        "benefits": "Обогащает почву кальцием\nНейтрализует кислотность почвы\nОтпугивает слизней и улиток",
        "application": "Промыть и высушить скорлупу\nИзмельчить в порошок\nДобавить в почву или компост",
        "suitable_plants": "Томаты\nПерцы\nБаклажаны\nЦветущие растения\nКактусы",
        "precautions": "Не использовать для растений, предпочитающих кислую почву\nПредварительно измельчать для лучшего усвоения"
    }
]

class Database:
    """Database class for interacting with MongoDB"""
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Will raise exception if cannot connect
            
            self.db = self.client[DB_NAME]
            self.vitamins = self.db[VITAMINS_COLLECTION]
            self.plants = self.db[PLANTS_COLLECTION]
            self.users = self.db[USERS_COLLECTION]
            self.feedback = self.db[FEEDBACK_COLLECTION]
            
            # Create indexes for faster lookups
            self.vitamins.create_index("name")
            self.plants.create_index("name")
            self.plants.create_index("waste_type")
            self.users.create_index("user_id", unique=True)
            
            logging.info("Connected to MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logging.error(f"Could not connect to MongoDB: {e}")
            # Continue without database - app will handle missing database gracefully
            self.client = None
            self.db = None
            self.vitamins = None
            self.plants = None
            self.users = None
            self.feedback = None
    
    def register_user(self, user_id, username, first_name=None):
        """Register new user or update existing user info"""
        if not self.users:
            logging.warning("Database not available - skipping user registration")
            return
        
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name or "",
                "last_interaction": datetime.now(),
                "interaction_count": 1,
                "favorite_sections": []
            }
            
            # Update user if exists, insert if not
            result = self.users.update_one(
                {"user_id": user_id},
                {"$set": user_data, "$setOnInsert": {"registered_at": datetime.now()}},
                upsert=True
            )
            
            if result.upserted_id:
                logging.info(f"New user registered: {username} (ID: {user_id})")
            else:
                logging.info(f"User info updated: {username} (ID: {user_id})")
        except Exception as e:
            logging.error(f"Error registering user: {e}")
    
    def update_user_interaction(self, user_id, section, query=None):
        """Update user interaction metrics"""
        if not self.users:
            logging.warning("Database not available - skipping user interaction update")
            return
        
        try:
            update_data = {
                "last_interaction": datetime.now(),
                "last_section": section
            }
            
            # Increment interaction count
            self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": update_data,
                    "$inc": {"interaction_count": 1},
                    "$push": {"interactions": {
                        "timestamp": datetime.now(),
                        "section": section,
                        "query": query
                    }}
                }
            )
            
            # Update favorite sections counter
            self.users.update_one(
                {"user_id": user_id, "favorite_sections.section": section},
                {"$inc": {"favorite_sections.$.count": 1}}
            )
            
            # If section not in favorite_sections, add it
            self.users.update_one(
                {"user_id": user_id, "favorite_sections.section": {"$ne": section}},
                {"$push": {"favorite_sections": {"section": section, "count": 1}}}
            )
        except Exception as e:
            logging.error(f"Error updating user interaction: {e}")
    
    def save_feedback(self, user_id, feedback_text):
        """Save user feedback"""
        if not self.feedback:
            logging.warning("Database not available - skipping feedback save")
            return False
        
        try:
            feedback_data = {
                "user_id": user_id,
                "feedback": feedback_text,
                "timestamp": datetime.now()
            }
            
            self.feedback.insert_one(feedback_data)
            logging.info(f"Feedback saved from user {user_id}")
            return True
        except Exception as e:
            logging.error(f"Error saving feedback: {e}")
            return False
    
    def get_vitamin_by_name(self, name):
        """Get vitamin information by name"""
        if not self.vitamins:
            logging.warning("Database not available - cannot get vitamin info")
            return None
        
        try:
            return self.vitamins.find_one({"name": name})
        except Exception as e:
            logging.error(f"Error retrieving vitamin: {e}")
            return None
    
    def get_all_vitamins(self):
        """Get all vitamins"""
        if not self.vitamins:
            logging.warning("Database not available - cannot get all vitamins")
            return []
        
        try:
            return list(self.vitamins.find())
        except Exception as e:
            logging.error(f"Error retrieving all vitamins: {e}")
            return []
    
    def search_vitamins(self, query):
        """Search vitamins by keyword"""
        if not self.vitamins:
            logging.warning("Database not available - cannot search vitamins")
            return []
        
        try:
            # Create a regex pattern for case-insensitive search
            pattern = {"$regex": query, "$options": "i"}
            
            # Search in name, aliases and description
            result = self.vitamins.find({
                "$or": [
                    {"name": pattern},
                    {"aliases": pattern},
                    {"short_description": pattern},
                    {"description": pattern}
                ]
            })
            
            return list(result)
        except Exception as e:
            logging.error(f"Error searching vitamins: {e}")
            return []
    
    def get_plant_tip_by_waste(self, waste_type):
        """Get plant care tip by waste type"""
        if not self.plants:
            logging.warning("Database not available - cannot get plant care tip")
            return None
        
        try:
            return self.plants.find_one({"waste_type": {"$regex": waste_type, "$options": "i"}})
        except Exception as e:
            logging.error(f"Error retrieving plant care tip: {e}")
            return None
    
    def get_all_plant_tips(self):
        """Get all plant care tips"""
        if not self.plants:
            logging.warning("Database not available - cannot get all plant care tips")
            return []
        
        try:
            return list(self.plants.find({"waste_type": {"$exists": True}}))
        except Exception as e:
            logging.error(f"Error retrieving all plant care tips: {e}")
            return []
    
    def search_plant_tips(self, query):
        """Search plant care tips by keyword"""
        if not self.plants:
            logging.warning("Database not available - cannot search plant care tips")
            return []
        
        try:
            # Create a regex pattern for case-insensitive search
            pattern = {"$regex": query, "$options": "i"}
            
            # Search in waste_type, short_description and description
            result = self.plants.find({
                "$and": [
                    {"waste_type": {"$exists": True}},  # Make sure it's a waste tip
                    {"$or": [
                        {"waste_type": pattern},
                        {"short_description": pattern},
                        {"description": pattern},
                        {"application": pattern},
                        {"suitable_plants": pattern}
                    ]}
                ]
            })
            
            return list(result)
        except Exception as e:
            logging.error(f"Error searching plant care tips: {e}")
            return []
            
    # New methods for plant database
    
    def get_plant_by_name(self, plant_name):
        """Get plant information by name."""
        if not self.plants:
            logging.warning("Database not available - cannot get plant info")
            return None
        
        try:
            # Try to find plant by exact name
            plant = self.plants.find_one({"name": plant_name})
            
            # If not found, try case-insensitive search
            if not plant:
                pattern = {"$regex": f"^{plant_name}$", "$options": "i"}
                plant = self.plants.find_one({"name": pattern})
                
            # If still not found, try partial match
            if not plant:
                pattern = {"$regex": plant_name, "$options": "i"}
                plant = self.plants.find_one({"name": pattern})
                
            return plant
        except Exception as e:
            logging.error(f"Error retrieving plant: {e}")
            return None
    
    def save_plant(self, plant_data):
        """Save or update plant information in the database."""
        # Check if plant already exists
        existing_plant = self.plants.find_one({"name": plant_data["name"]})
        
        if existing_plant:
            # Update existing plant
            self.plants.update_one(
                {"name": plant_data["name"]},
                {"$set": plant_data}
            )
            return existing_plant["_id"]
        else:
            # Insert new plant
            result = self.plants.insert_one(plant_data)
            return result.inserted_id
    
    def get_all_plants(self):
        """Get all plants from the database."""
        if not self.plants:
            logging.warning("Database not available - cannot get all plants")
            return []
        
        try:
            # Get all documents that have name but not waste_type
            # This differentiates plants from waste tips
            return list(self.plants.find({
                "name": {"$exists": True},
                "waste_type": {"$exists": False}
            }))
        except Exception as e:
            logging.error(f"Error retrieving all plants: {e}")
            return []
    
    def update_plant(self, plant_id, update_data):
        """Update an existing plant in the database"""
        if not self.plants:
            logging.warning("Database not available - cannot update plant")
            return False
        
        try:
            # Add last_updated timestamp
            update_data["last_updated"] = datetime.now()
            
            # Update plant
            result = self.plants.update_one(
                {"_id": plant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logging.info(f"Updated plant: {update_data.get('name', plant_id)}")
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"Error updating plant: {e}")
            return False
    
    def search_plants(self, query):
        """Search plants by keyword"""
        if not self.plants:
            logging.warning("Database not available - cannot search plants")
            return []
        
        try:
            # Create a regex pattern for case-insensitive search
            pattern = {"$regex": query, "$options": "i"}
            
            # Search in name, scientific_name and description
            # Exclude waste tips
            result = self.plants.find({
                "$and": [
                    {"waste_type": {"$exists": False}},  # Exclude waste tips
                    {"$or": [
                        {"name": pattern},
                        {"scientific_name": pattern},
                        {"description": pattern},
                        {"care_tips": pattern}
                    ]}
                ]
            })
            
            return list(result)
        except Exception as e:
            logging.error(f"Error searching plants: {e}")
            return []
    
    def increment_plant_image_count(self, plant_name):
        """Increment the count of images processed for a plant"""
        if not self.plants:
            logging.warning("Database not available - cannot update plant image count")
            return False
        
        try:
            result = self.plants.update_one(
                {"name": plant_name},
                {"$inc": {"image_count": 1}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error incrementing plant image count: {e}")
            return False
    
    def update_plant_extra_data(self, plant_name, field, value):
        """Update a specific field in the plant's extra_data."""
        self.plants.update_one(
            {"name": plant_name},
            {"$set": {f"extra_data.{field}": value}}
        )
        
    def search_plants_by_keyword(self, keyword):
        """Search for plants by keyword in name or description."""
        regex = {"$regex": keyword, "$options": "i"}
        return list(self.plants.find({
            "$or": [
                {"name": regex},
                {"scientific_name": regex},
                {"description": regex}
            ]
        }))

    def delete_plant(self, plant_name):
        """Delete a plant from the database."""
        self.plants.delete_one({"name": plant_name}) 