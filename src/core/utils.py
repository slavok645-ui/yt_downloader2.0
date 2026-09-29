import os
import re
import asyncio
from datetime import datetime

class Utils:
    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """
        Проверяет, является ли строка валидной ссылкой на YouTube.
        """
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(re.match(youtube_regex, url))

    @staticmethod
    def generate_filename(title: str, extension: str) -> str:
        """
        Создает безопасное имя файла с меткой времени,
        чтобы избежать перезаписи файлов с одинаковыми названиями.
        """
        # Убираем все, что не буквы и не цифры
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{timestamp}_{clean_title}.{extension}"

    @staticmethod
    async def get_file_size(file_path: str) -> float:
        """
        Возвращает размер файла в мегабайтах.
        Полезно для проверки лимитов Telegram (2 ГБ).
        """
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        return 0.0

    @staticmethod
    async def format_duration(seconds: int) -> str:
        """
        Превращает секунды в формат ЧЧ:ММ:СС.
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    async def trim_video(input_path: str, start_time: str, end_time: str) -> str:
        """
        Обрезает видео с помощью FFmpeg.
        start_time и end_time в формате HH:MM:SS или секундах.
        """
        output_path = input_path.replace(".mp4", "_trimmed.mp4")

        # Команда FFmpeg для быстрой обрезки без перекодирования (-c copy)
        # Если возникают проблемы с точностью, заменить -c copy на -c:v libx264
        command = [
            'ffmpeg', '-y',
            '-ss', start_time,
            '-to', end_time,
            '-i', input_path,
            '-c', 'copy',
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode == 0:
            return output_path
        else:
            raise Exception("Ошибка FFmpeg при обрезке")