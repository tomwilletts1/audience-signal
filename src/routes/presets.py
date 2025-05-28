# src/routes/presets.py
from flask import Blueprint, jsonify
from config import config 
from utils.logger import app_logger

def create_presets_blueprint():
    presets_bp = Blueprint('presets', __name__, url_prefix='/api')

    @presets_bp.route('/presets', methods=['GET'])
    def get_presets_route():
        try:
            app_logger.info("Presets data retrieved successfully via /presets route.")
            return jsonify({'status': 'success', 'presets': config['default'].PERSONA_PRESETS})
        except AttributeError: # Handles if PERSONA_PRESETS is not in config
            app_logger.error("PERSONA_PRESETS not found in config.", exc_info=True)
            return jsonify({'error': 'Presets configuration is missing.', 'status': 'error'}), 500
        except Exception as e:
            app_logger.error(f"Error in /api/presets route: {str(e)}", exc_info=True)
            return jsonify({'error': 'An internal error occurred while fetching presets.', 'status': 'error'}), 500
            
    return presets_bp 