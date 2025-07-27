# src/routes/api.py - Consolidated API Routes
from flask import Blueprint, request, jsonify, send_file
from src.utils.logger import app_logger
import os
import tempfile
import uuid

def create_api_blueprint(history_manager, audience_service, content_test_service, client_data_service):
    """Create consolidated API blueprint with all small routes."""
    
    api_bp = Blueprint('api', __name__, url_prefix='/api')

    # ==================== HISTORY ROUTES ====================
    @api_bp.route('/history', methods=['GET'])
    def get_history():
        """Get conversation history."""
        try:
            history = history_manager.get_history()
            return jsonify(history)
        except Exception as e:
            app_logger.error(f"Error getting history: {e}")
            return jsonify({'error': 'Failed to get history'}), 500

    @api_bp.route('/history', methods=['POST'])
    def add_to_history():
        """Add entry to history."""
        try:
            data = request.get_json()
            history_manager.add_to_history(data)
            return jsonify({'status': 'success'})
        except Exception as e:
            app_logger.error(f"Error adding to history: {e}")
            return jsonify({'error': 'Failed to add to history'}), 500

    # ==================== PRESET ROUTES ====================
    @api_bp.route('/presets', methods=['GET'])
    def get_presets():
        """Get available presets."""
        presets = [
            {"id": "retail", "name": "Retail Focus Group", "description": "Consumer retail preferences"},
            {"id": "tech", "name": "Technology Focus Group", "description": "Tech product feedback"},
            {"id": "healthcare", "name": "Healthcare Focus Group", "description": "Healthcare service feedback"}
        ]
        return jsonify(presets)

    # ==================== AUDIENCE ROUTES ====================
    @api_bp.route('/audiences', methods=['GET'])
    def get_audiences():
        """Get available audiences."""
        try:
            audiences = audience_service.get_all_audiences()
            return jsonify(audiences)
        except Exception as e:
            app_logger.error(f"Error getting audiences: {e}")
            return jsonify({'error': 'Failed to get audiences'}), 500

    @api_bp.route('/audiences', methods=['POST'])
    def create_audience():
        """Create a new audience."""
        try:
            data = request.get_json()
            audience = audience_service.create_audience(data)
            return jsonify(audience), 201
        except Exception as e:
            app_logger.error(f"Error creating audience: {e}")
            return jsonify({'error': 'Failed to create audience'}), 500

    # ==================== CONTENT TEST ROUTES ====================
    @api_bp.route('/test-content', methods=['POST'])
    def test_content():
        """Test content with audiences."""
        try:
            data = request.get_json()
            message = data.get('message', '')
            audience_id = data.get('audience_id', 'Young Professionals')
            
            results = content_test_service.test_message_with_audience(message, audience_id)
            return jsonify(results)
        except Exception as e:
            app_logger.error(f"Error testing content: {e}")
            return jsonify({'error': 'Failed to test content'}), 500

    # ==================== CLIENT DATA ROUTES ====================
    @api_bp.route('/client-data/upload', methods=['POST'])
    def upload_client_data():
        """Upload client data file."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            # Save file temporarily
            filename = f"{uuid.uuid4()}_{file.filename}"
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            file.save(temp_path)
            
            # Process file
            owner_id = request.form.get('owner_id', 'default')
            audience_name = request.form.get('audience_name', f'Custom_{uuid.uuid4().hex[:8]}')
            
            result = client_data_service.process_uploaded_file(temp_path, owner_id, audience_name)
            
            # Cleanup
            os.unlink(temp_path)
            
            return jsonify(result)
        except Exception as e:
            app_logger.error(f"Error uploading client data: {e}")
            return jsonify({'error': 'Failed to upload client data'}), 500

    # ==================== SUMMARY ROUTES ====================
    @api_bp.route('/summary', methods=['POST'])
    def generate_summary():
        """Generate summary from responses."""
        try:
            data = request.get_json()
            responses = data.get('responses', [])
            
            if not responses:
                return jsonify({'error': 'No responses provided'}), 400
            
            from src.services.summary import generate_summary_from_responses
            summary = generate_summary_from_responses(responses)
            
            return jsonify({'summary': summary})
        except Exception as e:
            app_logger.error(f"Error generating summary: {e}")
            return jsonify({'error': 'Failed to generate summary'}), 500

    # ==================== ANALYZE ROUTES ====================
    @api_bp.route('/analyze', methods=['POST'])
    def analyze_content():
        """Analyze content with vision/text."""
        try:
            data = request.get_json()
            content_type = data.get('type', 'text')
            content = data.get('content', '')
            personas = data.get('personas', [])
            
            if content_type == 'image':
                from src.services.vision import analyze_image
                results = []
                for persona in personas:
                    result = analyze_image(content, persona)
                    results.append({'persona': persona, 'result': result})
                return jsonify({'results': results})
            else:
                # Text analysis
                from src.services.persona import generate_persona_response
                results = []
                for persona in personas:
                    result = generate_persona_response(content, persona)
                    results.append({'persona': persona, 'result': result})
                return jsonify({'results': results})
                
        except Exception as e:
            app_logger.error(f"Error analyzing content: {e}")
            return jsonify({'error': 'Failed to analyze content'}), 500

    return api_bp 