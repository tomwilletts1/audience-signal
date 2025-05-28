# src/utils/history_manager.py
from datetime import datetime
from .logger import app_logger # Import app_logger

class HistoryManager:
    def __init__(self):
        self._response_history = []
        app_logger.info("HistoryManager initialized.")

    def add_entry(self, message, image_data, personas, results):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'image': bool(image_data),
            'personas': personas,
            'results': results
        }
        self._response_history.append(entry)
        app_logger.info(f"New entry added to history. Total entries: {len(self._response_history)}")

    def get_history(self):
        app_logger.info(f"Retrieving full history. {len(self._response_history)} entries found.")
        return self._response_history

    def clear_history(self):
        self._response_history = []
        app_logger.info("History cleared.") 