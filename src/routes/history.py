# src/routes/history.py
from flask import Blueprint, jsonify
from utils.history_manager import HistoryManager
from utils.logger import app_logger

def create_history_blueprint(history_manager_instance: HistoryManager):
    history_bp = Blueprint('history', __name__, url_prefix='/api')

    @history_bp.route('/history', methods=['GET'])
    def get_history_route():
        try:
            history_data = history_manager_instance.get_history()
            app_logger.info("History data retrieved successfully via /history route.")
            return jsonify(history_data)
        except Exception as e:
            app_logger.error(f"Error in /api/history route: {str(e)}", exc_info=True)
            return jsonify({'error': 'An internal error occurred while fetching history.', 'status': 'error'}), 500
            
    return history_bp 