from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="history", description="📜 История скачиваний"),
        BotCommand(command="failed", description="❌ Неудачные загрузки"),
        BotCommand(command="set_path", description="📁 Указать путь сохранения")
    ]
    await bot.set_my_commands(main_menu_commands)


def get_clear_history_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🗑️ Очистить историю",
        callback_data="clear_history")
    )
    return builder.as_markup()


def get_clear_failed_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🗑️ Очистить список ошибок",
        callback_data="clear_failed")
    )
    return builder.as_markup()
