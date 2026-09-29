import asyncio
import logging
from typing import Callable


class DownloadQueue:
    def __init__(self):
        # Сама очередь задач
        self.queue = asyncio.Queue()
        # Флаг работы воркера
        self.worker_task = None

    async def add_task(self, coro: Callable, *args, **kwargs):
        """Добавляет задачу в очередь"""
        await self.queue.put((coro, args, kwargs))
        logging.info(f"Задача добавлена в очередь. Всего в очереди: {self.queue.qsize()}")

    async def start_worker(self):
        """Запускает бесконечный цикл обработки очереди"""
        if self.worker_task:
            return

        self.worker_task = asyncio.create_task(self._worker())
        logging.info("Воркер очереди запущен.")

    async def _worker(self):
        while True:
            # Ждем появления задачи в очереди
            coro, args, kwargs = await self.queue.get()
            try:
                logging.info(f"Начинаю выполнение задачи из очереди...")
                # Выполняем само скачивание
                await coro(*args, **kwargs)
            except Exception as e:
                logging.error(f"Ошибка при выполнении задачи из очереди: {e}")
            finally:
                # Помечаем задачу как выполненную
                self.queue.task_done()
                logging.info(f"Задача завершена. Осталось в очереди: {self.queue.qsize()}")


# Создаем глобальный объект очереди
download_manager = DownloadQueue()