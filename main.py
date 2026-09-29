import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Импорты роутеров
from src.handlers import video_handler, commands_handler, admin_handler
# Функция для меню
from src.keyboards.main_kb import set_main_menu
# Импортируем менеджер очереди (предположим, вы создали его в src/core/manager.py)
from src.core.downloader import download_manager

from config import BOT_TOKEN
from src.core.database_mgr import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


async def main():
    # 1. Инициализация базы данных
    db = DatabaseManager()

    # 2. Инициализация бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    # 3. Инициализация диспетчера
    dp = Dispatcher()

    # --- Установка меню команд ---
    try:
        await set_main_menu(bot)
        logging.info("Меню команд успешно установлено.")
    except Exception as e:
        logging.error(f"Не удалось установить меню команд: {e}")

    # 4. Регистрация роутеров
    dp.include_router(commands_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(video_handler.router)

    # --- НОВОЕ: Запуск воркера очереди ---
    # Это позволит обрабатывать скачивания строго по одному в фоне
    asyncio.create_task(download_manager.start_worker())
    logging.info("Воркер очереди скачивания запущен.")

    # 5. Запуск бота
    logging.info("Бот запущен и готов к работе...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Передаем объекты через контекст диспетчера, чтобы они были доступны в хендлерах
    await dp.start_polling(bot, db=db)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот выключен пользователем")