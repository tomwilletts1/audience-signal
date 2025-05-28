# src/routes/analyze.py
from flask import Blueprint, request, jsonify
from services.persona import generate_persona_response
from services.vision import analyze_image, analyze_combined
from utils.history_manager import HistoryManager 
from utils.logger import app_logger 

def create_analyze_blueprint(history_manager_instance: HistoryManager):
    analyze_bp = Blueprint('analyze', __name__, url_prefix='/api') 

    @analyze_bp.route('/analyze', methods=['POST'])
    def analyze_message_route():
        try:
            data = request.get_json()
            if not data:
                app_logger.warning("No data provided in /analyze request")
                return jsonify({'error': 'No data provided', 'status': 'error'}), 400

            message = data.get('message')
            personas_details = data.get('personas', []) 
            image_data = data.get('image')

            if not personas_details:
                app_logger.warning("Personas are required in /analyze request")
                return jsonify({'error': 'Personas are required', 'status': 'error'}), 400
            if not message and not image_data:
                app_logger.warning("Either message or image is required in /analyze request")
                return jsonify({'error': 'Either message or image is required', 'status': 'error'}), 400

            results = []
            for persona_detail in personas_details: 
                response_content = None
                if image_data and message:
                    response_content = analyze_combined(image_data, message, persona_detail)
                elif image_data:
                    response_content = analyze_image(image_data, persona_detail)
                else: 
                    response_content = generate_persona_response(message, persona_detail)

                results.append({'persona': persona_detail, 'response': response_content})

            history_manager_instance.add_entry(message, image_data, personas_details, results)
            app_logger.info(f"Analysis successful for {len(personas_details)} personas.")
            return jsonify({'results': results, 'status': 'success'})

        except Exception as e:
            app_logger.error(f"Error in /api/analyze route: {str(e)}", exc_info=True)
            return jsonify({'error': f'An internal error occurred.', 'status': 'error'}), 500
            
    return analyze_bp 