from flask import Blueprint, request, jsonify
# Import from the new services.summary module
from services.summary import generate_summary_from_responses 
from utils.logger import app_logger

def create_summary_blueprint():
    summary_bp = Blueprint('summary_route', __name__, url_prefix='/api')

    @summary_bp.route('/summary', methods=['POST'])
    def generate_response_summary_route():
        try:
            data = request.get_json()
            if not data or 'responses' not in data:
                app_logger.warning("No responses provided for summary generation.")
                return jsonify({'error': 'No responses provided', 'status': 'error'}), 400

            # Use the function from services.summary
            summary_text = generate_summary_from_responses(data['responses'])
            
            # Check if the service returned an error string
            if summary_text.startswith("Error generating summary:"):
                app_logger.error(f"Summary service returned an error: {summary_text}")
                # You might want to return a more generic error to the client
                return jsonify({'error': 'Failed to generate summary.', 'status': 'error'}), 500

            app_logger.info("Summary generated successfully by route.")
            return jsonify({'summary': summary_text, 'status': 'success'})
        except Exception as e:
            app_logger.error(f"Error in /api/summary route: {str(e)}", exc_info=True)
            return jsonify({'error': 'An internal error occurred.', 'status': 'error'}), 500
            
    return summary_bp 