from aiogram import Router, F, Bot
from aiogram.types import Message
from config import ADMIN_ID  # Импортируй свой ID

router = Router()


@router.message(F.document, F.from_user.id == ADMIN_ID)
async def update_cookies(message: Message, bot: Bot):
    # Проверяем, что файл называется cookies.txt
    if message.document.file_name == "cookies.txt":
        # Путь, куда сохранить файл (корень проекта)
        # Если бот запущен из корня, то путь будет просто 'cookies.txt'
        destination = "cookies.txt"

        # Скачиваем файл
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, destination)

        await message.answer("**Файл cookies.txt успешно обновлен!**\nТеперь я использую новые данные для YouTube.")
    else:
        await message.answer("Я принимаю только файлы с названием `cookies.txt`.")