import os
import asyncio
from typing import Any, Dict, Optional
import yt_dlp
from tqdm import tqdm

class YTDownloader:
    def __init__(self, download_path: str = "downloads/") -> None:
        self.base_path = os.getcwd()
        self.download_path = os.path.join(self.base_path, download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path, exist_ok=True)

    def _get_common_opts(self) -> Dict[str, Any]:
        cookie_path = os.path.join(self.base_path, 'youtube_cookies.txt')
        return {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookie_path,
            'cache_dir': os.path.join(self.download_path, '.cache'),
            'js_runtimes': {'deno': {}},
            'allow_remote_scripts': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'ios', 'web', 'tv'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }

    def get_info(self, url: str) -> Optional[Dict[str, Any]]:
        opts = self._get_common_opts()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl: # type: ignore
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                return {
                    'title': str(info.get('title', 'No Title')),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail')
                }
        except Exception as e:
            print(f"Ошибка получения инфо: {e}")
            return None

    async def download(self, url: str) -> str:
        def _download() -> str:
            pbar: Optional[tqdm] = None

            def progress_hook(d: Dict[str, Any]) -> None:
                nonlocal pbar
                if d.get('status') == 'downloading':
                    total_val = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_val = d.get('downloaded_bytes', 0)

                    if pbar is None and total_val is not None:
                        pbar = tqdm(
                            total=float(total_val),
                            unit='B',
                            unit_scale=True,
                            desc="📥 Скачивание",
                            colour='green',
                            leave=False
                        )

                    if pbar is not None and downloaded_val is not None:
                        pbar.n = float(downloaded_val)
                        pbar.refresh()

                elif d.get('status') == 'finished':
                    if pbar is not None:
                        pbar.close()
                        pbar = None

            opts = self._get_common_opts()
            opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'ffmpeg_location': r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe',
            })

            with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore
                ydl.cache.remove()
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise RuntimeError("Не удалось загрузить видео")

                return str(ydl.prepare_filename(info))

        return await asyncio.to_thread(_download)


class DownloadManager:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def add_to_queue(self, task_func, *args):
        """Добавляет задачу в очередь"""
        await self.queue.put((task_func, args))

    async def start_worker(self):
        """Воркер, который обрабатывает задачи по одной"""
        print("Воркер очереди скачивания запущен...")
        while True:
            # Ждем новую задачу
            task_func, args = await self.queue.get()
            try:
                # Выполняем функцию скачивания
                await task_func(*args)
            except Exception as e:
                print(f"Ошибка в воркере: {e}")
            finally:
                # Помечаем задачу как завершенную
                self.queue.task_done()

# Создаем экземпляры для импорта в другие файлы
download_manager = DownloadManager()
yt_downloader = YTDownloader()