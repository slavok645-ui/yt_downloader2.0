import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
# Импортируем только то, что реально используем
from aiogram.exceptions import AiogramError

from src.core.database_mgr import DatabaseManager
from src.keyboards.main_kb import get_clear_history_kb, get_clear_failed_kb

router = Router()
db = DatabaseManager()

last_messages = {}
user_folders = {}


class FolderStates(StatesGroup):
    waiting_for_path = State()


def escape_md(text: str) -> str:
    """Экранирует спецсимволы MarkdownV1."""
    if not text: return ""
    for char in ['_', '*', '`', '[']:
        text = text.replace(char, f'\\{char}')
    return text


async def clear_previous(message: Message):
    """Удаляет команду пользователя и сообщение бота, используя точные исключения."""
    user_id = message.from_user.id
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except AiogramError:
        pass  # Игнорируем только ошибки Telegram (например, сообщение уже удалено)

    # Удаляем старый ответ бота
    if user_id in last_messages:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_messages[user_id])
        except AiogramError:
            pass

@router.message(CommandStart())
async def command_start_handler(message: Message):
    await clear_previous(message)
    sent_msg = await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Бот для скачивания готов к работе.\n"
        "Для обрезки ввести ссылку в формате:\n"
        "Ссылка 1:00 1:53\n"
        "Используйте `/` для управления."
    )
    last_messages[message.from_user.id] = sent_msg.message_id


@router.message(Command("history"))
async def command_history_handler(message: Message):
    await clear_previous(message)
    history = db.get_user_history(message.from_user.id)
    if not history:
        sent_msg = await message.answer("📂 История пуста.")
        last_messages[message.from_user.id] = sent_msg.message_id
        return

    lines = [f"🔹 {escape_md(h[0])}" for h in history]
    text = "📜 *История скачиваний:*\n\n" + "\n".join(lines)

    sent_msg = await message.answer(
        text,
        reply_markup=get_clear_history_kb(),
        parse_mode="Markdown"
    )
    last_messages[message.from_user.id] = sent_msg.message_id


@router.callback_query(F.data == "clear_history")
async def process_clear_history(callback: CallbackQuery):
    db.clear_history(callback.from_user.id)
    await callback.message.edit_text("История очищена!")
    await callback.answer()


@router.message(Command("set_path"))
async def cmd_set_path(message: Message, state: FSMContext):
    await clear_previous(message)
    sent_msg = await message.answer(
        " *Отправьте полный путь к папке.*\n\n"
        "Пример для Windows: `C:\\Downloads\\YT`"
    )
    last_messages[message.from_user.id] = sent_msg.message_id
    await state.set_state(FolderStates.waiting_for_path)


@router.message(FolderStates.waiting_for_path)
async def process_path_input(message: Message, state: FSMContext):
    new_path = message.text.strip()
    user_id = message.from_user.id

    try:
        await message.delete()
    except AiogramError:
        pass

    try:
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)

        user_folders[user_id] = new_path

        if user_id in last_messages:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_messages[user_id])
            except AiogramError:
                pass

        sent_msg = await message.answer(f"Путь изменен на:\n`{escape_md(new_path)}`", parse_mode="Markdown")
        last_messages[user_id] = sent_msg.message_id
        await state.clear()

    except OSError as e:  # Перехватываем только ошибки системы (права доступа, неверный путь)
        msg = await message.answer(f"Ошибка пути: {escape_md(str(e))}\n\nПопробуйте другой:")
        last_messages[user_id] = msg.message_id


@router.message(Command("failed"))
async def command_failed_handler(message: Message):
    await clear_previous(message)

    failed = db.get_failed_links(message.from_user.id)
    if not failed:
        sent_msg = await message.answer("Список ошибок пуст!")
        last_messages[message.from_user.id] = sent_msg.message_id
        return

    text_parts = ["*Неудачные попытки:*"]
    for url, reason, date in failed:
        safe_url = escape_md(url)
        safe_reason = escape_md(reason[:100])
        text_parts.append(f"🔗 {safe_url}\n💬 Ошибка: `{safe_reason}`\n📅 {date}\n")

    text = "\n".join(text_parts)

    try:
        sent_msg = await message.answer(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_clear_failed_kb()
        )
        last_messages[message.from_user.id] = sent_msg.message_id
    except AiogramError:
        # Резервный вариант без разметки
        sent_msg = await message.answer(
            "Ошибки загрузки (текст без разметки):\n" + text.replace("*", "").replace("`", ""),
            reply_markup=get_clear_failed_kb()
        )
        last_messages[message.from_user.id] = sent_msg.message_id


@router.callback_query(F.data == "clear_failed")
async def process_clear_failed(callback: CallbackQuery):
    db.clear_failed_history(callback.from_user.id)
    await callback.message.edit_text("Список ошибок очищен!")
    await callback.answer()