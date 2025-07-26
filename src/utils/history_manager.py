# src/utils/history_manager.py
from datetime import datetime
import json
from src.utils.logger import app_logger
from src.database import get_db_connection

class HistoryManager:
    def __init__(self):
        # The connection is now managed by the get_db_connection function
        app_logger.info("HistoryManager initialized.")

    def add_entry(self, message, image_data, personas, results):
        conn = get_db_connection()
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'image': bool(image_data),
                'personas': personas,
                'results': results
            }
            conn.cursor().execute(
                "INSERT INTO history (timestamp, message, image, personas, results) VALUES (?, ?, ?, ?, ?)",
                (
                    entry['timestamp'],
                    entry['message'],
                    1 if entry['image'] else 0,
                    json.dumps(entry['personas']),
                    json.dumps(entry['results'])
                ),
            )
            conn.commit()
            app_logger.info("New entry added to history database.")
        finally:
            conn.close()

    def get_history(self):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, message, image, personas, results FROM history ORDER BY timestamp DESC")
            rows = cursor.fetchall()
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
            app_logger.info(f"Retrieving full history. {len(history)} entries found.")
            return history
        finally:
            conn.close()

    def clear_history(self):
        conn = get_db_connection()
        try:
            conn.cursor().execute("DELETE FROM history")
            conn.commit()
            app_logger.info("History cleared from database.")
        finally:
            conn.close()
