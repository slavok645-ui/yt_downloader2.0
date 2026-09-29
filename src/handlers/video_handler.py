import logging
import os
import asyncio
from typing import Any, Optional
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.exceptions import AiogramError
from yt_dlp.utils import DownloadError

from src.core.downloader import yt_downloader, download_manager
from src.core.database_mgr import DatabaseManager
from src.core.utils import Utils
from src.handlers.commands_handler import user_folders, last_messages

router = Router()
db = DatabaseManager()


def escape_md(text: Any) -> str:
    """Безопасное экранирование Markdown (защита от None)."""
    if text is None:
        return "Без названия"

    # Принудительно приводим к строке
    safe_text = str(text)
    for char in ['_', '*', '`', '[']:
        safe_text = safe_text.replace(char, f'\\{char}')
    return safe_text


async def safe_edit(message: Message, text: str, parse_mode: Optional[str] = "Markdown") -> Message:
    """Редактирует сообщение или отправляет новое, если старое удалено."""
    try:
        # Пытаемся редактировать
        return await message.edit_text(text, parse_mode=parse_mode)
    except AiogramError:
        # Если сообщение удалено (Bad Request), отправляем новое
        return await message.answer(text, parse_mode=parse_mode)


# --- ФУНКЦИЯ-ОБРАБОТЧИК (Worker Task) ---
async def process_download_task(message: Message, _bot: Bot, url: str, start_time: Optional[str],
                                end_time: Optional[str], status_msg: Message):
    user_id = message.from_user.id
    current_path = user_folders.get(user_id, "downloads/")
    yt_downloader.download_path = current_path

    # Инициализация переменной пути
    final_file_path: str = ""
    current_status: Message = status_msg

    try:
        # 1. Получение информации
        info = await asyncio.to_thread(yt_downloader.get_info, url)
        if not info:
            raise ValueError("YouTube не вернул данные. Проверьте ссылку.")

        title = str(info.get('title', 'Без названия'))
        current_status = await safe_edit(current_status, f"⏳ Начинаю загрузку:\n* {escape_md(title)} *")

        # 2. Скачивание
        try:
            # Метод download должен возвращать строку с путем
            downloaded_path = await yt_downloader.download(url)
            final_file_path = str(downloaded_path)
        except DownloadError as de:
            raise RuntimeError(f"Сбой загрузки: {str(de)}")

        # 3. Обрезка
        if start_time and end_time and os.path.exists(final_file_path):
            try:
                current_status = await safe_edit(
                    current_status,
                    f"Обрезаю фрагмент: `{escape_md(start_time)}` — `{escape_md(end_time)}`..."
                )

                trimmed_path = await Utils.trim_video(final_file_path, start_time, end_time)

                if trimmed_path and os.path.exists(trimmed_path):
                    # Удаляем оригинал только после подтверждения создания нового файла
                    if os.path.exists(final_file_path):
                        os.remove(final_file_path)
                    final_file_path = str(trimmed_path)
                    title = f"[TRIM] {title}"
            except OSError as trim_err:
                logging.error(f"Ошибка обрезки: {trim_err}")
                await message.answer(f"Ошибка обрезки: {escape_md(str(trim_err))}")

        # 4. Финальный результат
        if final_file_path and os.path.exists(final_file_path):
            # Теперь final_file_path используется — предупреждение исчезнет
            file_size_mb = os.path.getsize(final_file_path) / (1024 * 1024)

            final_text = (
                f"✅ *Готово!*\n\n"
                f"🎬 Название: `{escape_md(title)}`\n"
                f"📦 Размер: `{file_size_mb:.2f} MB`"
            )
            await safe_edit(current_status, final_text)
            db.add_history(user_id, title, url)
        else:
            raise FileNotFoundError("Файл не найден на диске после загрузки.")

    except (ValueError, RuntimeError, FileNotFoundError, OSError) as known_err:
        # Ловим только предсказуемые ошибки
        logging.warning(f"Ожидаемая ошибка обработки: {known_err}")
        db.add_failed_link(user_id, url, str(known_err))
        await safe_edit(current_status, f"❌ Ошибка: {known_err}", parse_mode=None)

    except Exception as e:
        # Критический сбой (оставляем для воркера, чтобы он не "умер" совсем)
        logging.exception(f"Критический сбой: {e}")
        db.add_failed_link(user_id, url, "Внутренняя ошибка сервера")
        await safe_edit(current_status, "Критический сбой при обработке.", parse_mode=None)


# --- ХЕНДЛЕР (Главная точка входа) ---
@router.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_video_download(message: Message, bot: Bot):
    user_id = message.from_user.id

    # Очистка чата
    try:
        await message.delete()
        if user_id in last_messages:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_messages[user_id])
    except AiogramError:
        pass

    # Парсинг сообщения
    parts = message.text.split()
    url = parts[0]
    start_time, end_time = None, None

    # Поддержка форматов: "URL 00:01 00:30" или "URL 00:01-00:30"
    if len(parts) == 3:
        start_time, end_time = parts[1], parts[2]
    elif len(parts) == 2 and "-" in parts[1]:
        try:
            t_parts = parts[1].split("-")
            if len(t_parts) == 2:
                start_time, end_time = t_parts[0], t_parts[1]
        except (ValueError, IndexError):
            pass

    status_msg = await message.answer("Добавлено в очередь...")
    last_messages[user_id] = status_msg.message_id

    # Передача в менеджер очередей
    await download_manager.add_to_queue(
        process_download_task,
        message, bot, url, start_time, end_time, status_msg
    )