import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/database.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            # Таблица успешных загрузок
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    url TEXT,
                    date TEXT
                )
            """)
            # НОВАЯ: Таблица неудачных попыток
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS failed_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    url TEXT,
                    reason TEXT,
                    date TEXT
                )
            """)

    # --- Методы для успешной истории ---

    def add_history(self, user_id, title, url):
        with self.conn:
            self.conn.execute(
                "INSERT INTO history (user_id, title, url, date) VALUES (?, ?, ?, ?)",
                (user_id, title, url, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )

    def get_user_history(self, user_id, limit=5):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT title, url, date FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return cursor.fetchall()

    def clear_history(self, user_id: int):
        with self.conn:
            self.conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))

    # --- НОВЫЕ: Методы для неудачных загрузок ---

    def add_failed_link(self, user_id, url, reason):
        """Записывает ошибку при скачивании в базу"""
        with self.conn:
            self.conn.execute(
                "INSERT INTO failed_links (user_id, url, reason, date) VALUES (?, ?, ?, ?)",
                (user_id, url, str(reason), datetime.now().strftime("%Y-%m-%d %H:%M"))
            )

    def get_failed_links(self, user_id, limit=10):
        """Возвращает список последних ошибок"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT url, reason, date FROM failed_links WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return cursor.fetchall()

    def clear_failed_history(self, user_id: int):
        """Очищает список ошибок пользователя"""
        with self.conn:
            self.conn.execute("DELETE FROM failed_links WHERE user_id = ?", (user_id,))