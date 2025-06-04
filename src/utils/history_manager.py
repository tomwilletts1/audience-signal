# src/utils/history_manager.py
from datetime import datetime
import json
import sqlite3
from .logger import app_logger  # Import app_logger

class HistoryManager:
    def __init__(self, db_path="history.db"):
        self.db_path = db_path
        self._connect()
        self._create_table()
        app_logger.info("HistoryManager initialized with database %s.", db_path)

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                message TEXT,
                image INTEGER,
                personas TEXT,
                results TEXT
            )
            """
        )
        self.conn.commit()

    def add_entry(self, message, image_data, personas, results):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'image': bool(image_data),
            'personas': personas,
            'results': results
        }
        self.cursor.execute(
            "INSERT INTO history (timestamp, message, image, personas, results) VALUES (?, ?, ?, ?, ?)",
            (
                entry['timestamp'],
                entry['message'],
                1 if entry['image'] else 0,
                json.dumps(entry['personas']),
                json.dumps(entry['results'])
            ),
        )
        self.conn.commit()
        app_logger.info("New entry added to history database.")

    def get_history(self):
        self.cursor.execute("SELECT timestamp, message, image, personas, results FROM history")
        rows = self.cursor.fetchall()
        history = []
        for row in rows:
            history.append(
                {
                    'timestamp': row['timestamp'],
                    'message': row['message'],
                    'image': bool(row['image']),
                    'personas': json.loads(row['personas']),
                    'results': json.loads(row['results']),
                }
            )
        app_logger.info("Retrieving full history. %d entries found.", len(history))
        return history

    def clear_history(self):
        self.cursor.execute("DELETE FROM history")
        self.conn.commit()
        app_logger.info("History cleared from database.")

    def __del__(self):
        try:
            self.conn.close()
        except Exception:
            pass
