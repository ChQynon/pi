import os
import sys
import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import bot

async def main():
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("bot.log"),
                logging.StreamHandler()
            ]
        )
        
        # Initialize bot and dispatcher
        storage = MemoryStorage()
        
        # Custom session if needed for proxy support
        # session = AiohttpSession(proxy="http://proxy.server:1080")
        # bot_instance = Bot(token=BOT_TOKEN, session=session)
        
        bot_instance = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=storage)
        
        # Register the router
        dp.include_router(bot.router)
        
        # Register startup and shutdown handlers
        dp.startup.register(bot.on_startup)
        dp.shutdown.register(bot.on_shutdown)
        
        # Start polling
        await bot_instance.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot_instance, allowed_updates=dp.resolve_used_update_types())
    
    except Exception as e:
        logging.critical(f"Bot crashed: {e}")
        traceback.print_exc()
        
        # Show error message in console and keep it open
        print("\n\n")
        print("=" * 50)
        print("CRITICAL ERROR - BOT CRASHED")
        print("=" * 50)
        print(f"Error: {e}")
        print("\nCheck the log file for more details.")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")
        print("Bot stopped. Press Enter to exit...")
        input()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input() 