# src/routes/focus_group.py
from flask import Blueprint, request, jsonify
from src.services.focus_group_service import FocusGroupSimulator, PersonaStyle
from src.utils.logger import app_logger
import uuid
from src.services.audience_service import AudienceService

# Forward declaration for type hinting
# AudienceService = Type('AudienceService')

def create_focus_group_blueprint(audience_service: AudienceService):
    focus_group_bp = Blueprint('focus_group', __name__, url_prefix='/api/focus_group')

    # Store active simulations (in production, use Redis or database)
    active_simulations = {}

    @focus_group_bp.route('/simulate', methods=['POST'])
    def simulate_focus_group_route():
        try:
            data = request.get_json()
            if not data:
                app_logger.warning("No data provided for focus group simulation.")
                return jsonify({'error': 'No data provided', 'status': 'error'}), 400

            audience_id = data.get('audience_id')
            personas_details = data.get('personas') # For legacy or direct persona input
            questions = data.get('questions', [])
            group_size = data.get('group_size')
            open_discussion = data.get('open_discussion', False)
            
            if not audience_id and not personas_details:
                return jsonify({'error': 'Either audience_id or a list of personas is required.', 'status': 'error'}), 400

            if audience_id:
                app_logger.info(f"Simulating focus group for audience_id: {audience_id}")
                sample_count = int(group_size) if group_size else 8
                personas_details = audience_service.sample_personas_from_audience(audience_id, count=sample_count)

            stimulus_message = data.get('message')
            stimulus_image_data = data.get('image_data') 
            num_discussion_rounds = data.get('num_discussion_rounds', 1)
            num_discussion_rounds = int(num_discussion_rounds)
            persona_styles = data.get('persona_styles', {})
            moderator_questions = data.get('moderator_questions', [])

            if not stimulus_message and not stimulus_image_data:
                return jsonify({'error': 'Either message or image_data is required for stimulus.', 'status': 'error'}), 400
            
            simulator = FocusGroupSimulator(
                personas_details=personas_details,
                stimulus_message=stimulus_message,
                stimulus_image_data=stimulus_image_data,
                questions=questions,
                group_size=group_size,
                open_discussion=open_discussion
            )
            
            # Set persona styles
            for persona_idx_str, style_str in persona_styles.items():
                try:
                    persona_idx = int(persona_idx_str)
                    style = PersonaStyle(style_str)
                    simulator.set_persona_style(persona_idx, style)
                except (ValueError, KeyError) as e:
                    app_logger.warning(f"Invalid persona style: {persona_idx_str}={style_str}, error: {e}")
            
            # Add moderator questions (legacy)
            for mq in moderator_questions:
                simulator.add_moderator_question(mq.get('question'), mq.get('after_round'))
            
            # Generate simulation ID and store for live control
            simulation_id = str(uuid.uuid4())
            active_simulations[simulation_id] = simulator
            
            # Run simulation
            result = simulator.run_simulation(num_discussion_rounds=num_discussion_rounds)
            
            # Clean up completed simulation
            if result.get('status') == 'completed':
                if simulation_id in active_simulations:
                    del active_simulations[simulation_id]
            
            result['simulation_id'] = simulation_id
            return jsonify(result)

        except ValueError as ve:
            app_logger.error(f"ValueError in focus group simulation: {str(ve)}", exc_info=True)
            return jsonify({'error': str(ve), 'status': 'error'}), 400
        except Exception as e:
            app_logger.error(f"Error in /api/focus_group/simulate: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error during focus group simulation.', 'status': 'error'}), 500
            
    @focus_group_bp.route('/start_live', methods=['POST'])
    def start_live_simulation():
        """Start a live simulation that can be controlled in real-time."""
        try:
            data = request.get_json()
            
            personas = data.get('personas', [])
            message = data.get('message')
            image_data = data.get('image_data')
            persona_styles = data.get('persona_styles', {})
            
            if not personas:
                return jsonify({'status': 'error', 'error': 'At least one persona is required'}), 400
            
            if not message and not image_data:
                return jsonify({'status': 'error', 'error': 'Either message or image is required'}), 400
            
            # Create simulator
            simulator = FocusGroupSimulator(
                personas_details=personas,
                stimulus_message=message,
                stimulus_image_data=image_data
            )
            
            # Set persona styles
            for persona_idx_str, style_str in persona_styles.items():
                try:
                    persona_idx = int(persona_idx_str)
                    style = PersonaStyle(style_str)
                    simulator.set_persona_style(persona_idx, style)
                except (ValueError, KeyError):
                    app_logger.warning(f"Invalid persona style: {persona_idx_str}={style_str}")
            
            # Generate simulation ID and store
            simulation_id = str(uuid.uuid4())
            active_simulations[simulation_id] = simulator
            
            # Run initial reactions only (round 0)
            result = simulator.run_simulation(0)  # 0 discussion rounds = initial reactions only
            
            return jsonify({
                'status': 'live_started',
                'simulation_id': simulation_id,
                'initial_transcript': result.get('transcript', []),
                'state': simulator.get_simulation_state()
            })
            
        except Exception as e:
            app_logger.error(f"Error starting live simulation: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/inject_question', methods=['POST'])
    def inject_moderator_question(simulation_id):
        """Inject a moderator question into a live simulation."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            data = request.get_json()
            question = data.get('question')
            
            if not question:
                return jsonify({'status': 'error', 'error': 'Question is required'}), 400
            
            simulator = active_simulations[simulation_id]
            result = simulator.inject_question(question)
            
            return jsonify({
                'status': 'success',
                'result': result,
                'state': simulator.get_simulation_state()
            })
            
        except Exception as e:
            app_logger.error(f"Error injecting question: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/continue_round', methods=['POST'])
    def continue_discussion_round(simulation_id):
        """Continue with the next discussion round in a live simulation."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            simulator = active_simulations[simulation_id]
            
            # Continue with one more discussion round
            result = simulator.run_simulation(1)
            
            # Clean up if completed
            if result.get('status') == 'completed':
                del active_simulations[simulation_id]
            
            return jsonify({
                'status': 'success',
                'result': result,
                'state': simulator.get_simulation_state()
            })
            
        except Exception as e:
            app_logger.error(f"Error continuing discussion round: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/pause', methods=['POST'])
    def pause_simulation(simulation_id):
        """Pause a live simulation."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            simulator = active_simulations[simulation_id]
            simulator.pause_simulation()
            
            return jsonify({
                'status': 'success',
                'message': 'Simulation paused',
                'state': simulator.get_simulation_state()
            })
            
        except Exception as e:
            app_logger.error(f"Error pausing simulation: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/resume', methods=['POST'])
    def resume_simulation(simulation_id):
        """Resume a paused simulation."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            simulator = active_simulations[simulation_id]
            simulator.resume_simulation()
            
            return jsonify({
                'status': 'success',
                'message': 'Simulation resumed',
                'state': simulator.get_simulation_state()
            })
            
        except Exception as e:
            app_logger.error(f"Error resuming simulation: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/state', methods=['GET'])
    def get_simulation_state(simulation_id):
        """Get the current state of a live simulation."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            simulator = active_simulations[simulation_id]
            
            return jsonify({
                'status': 'success',
                'state': simulator.get_simulation_state(),
                'transcript': simulator.transcript
            })
            
        except Exception as e:
            app_logger.error(f"Error getting simulation state: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/analytics', methods=['GET'])
    def get_simulation_analytics(simulation_id):
        """Get analytics for a simulation (active or completed)."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            simulator = active_simulations[simulation_id]
            analytics = simulator._generate_analytics()
            
            return jsonify({
                'status': 'success',
                'analytics': analytics
            })
            
        except Exception as e:
            app_logger.error(f"Error getting analytics: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @focus_group_bp.route('/<simulation_id>/complete', methods=['POST'])
    def complete_simulation(simulation_id):
        """Manually complete and cleanup a simulation."""
        try:
            if simulation_id not in active_simulations:
                return jsonify({'status': 'error', 'error': 'Simulation not found or not active'}), 404
            
            simulator = active_simulations[simulation_id]
            analytics = simulator._generate_analytics()
            
            # Cleanup
            del active_simulations[simulation_id]
            
            return jsonify({
                'status': 'success',
                'message': 'Simulation completed and cleaned up',
                'final_analytics': analytics
            })
            
        except Exception as e:
            app_logger.error(f"Error completing simulation: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'error': str(e)}), 500

    return focus_group_bp 