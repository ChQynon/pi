from aiogram.dispatcher.filters.state import State, StatesGroup

class UserState(StatesGroup):
    """User states for handling conversations"""
    waiting_for_query = State()  # Waiting for user query
    waiting_for_vitamin_name = State()  # Waiting for vitamin name
    waiting_for_plant_image = State()  # Waiting for plant image
    waiting_for_feedback = State()  # Waiting for user feedback
    waiting_for_plant_name = State()  # Waiting for plant name for care tips 