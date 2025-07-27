# src/routes/focus_group.py
from flask import Blueprint, request, jsonify
from src.services.focus_group_service import FocusGroupSimulator, PersonaStyle
from src.utils.logger import app_logger
import uuid
from src.services.audience_service import AudienceService

# Forward declaration for type hinting
# AudienceService = Type('AudienceService')

def create_focus_group_blueprint(audience_service: AudienceService, data_service):
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
                
                # Check if this is a city audience
                if audience_id in ["Manchester", "Birmingham", "Liverpool", "London", "Leeds", "Newcastle", "Cardiff", "Oxford", "Norwich"]:
                    try:
                        # Get city audience data using consolidated data service
                        city_audience = data_service.create_city_audience(audience_id)
                        # Use the personas from the city data
                        personas_details = city_audience['personas']
                        app_logger.info(f"Using city audience for {audience_id}: {len(personas_details)} personas")
                    except Exception as e:
                        app_logger.error(f"Error creating city audience for {audience_id}: {e}")
                        return jsonify({'error': f'Failed to create city audience for {audience_id}', 'status': 'error'}), 500
                else:
                    # Use regular audience service
                    personas_details = audience_service.sample_personas_from_audience(audience_id, count=sample_count)

            if not personas_details:
                return jsonify({'error': 'No personas could be generated for the audience.', 'status': 'error'}), 400

            app_logger.info(f"Starting focus group with {len(personas_details)} personas")

            # Extract simulation parameters
            stimulus_message = data.get('message', '')
            stimulus_image_data = data.get('image_data')
            moderator_questions = questions if questions else []
            num_discussion_rounds = data.get('discussion_rounds', 1)

            # Generate simulation ID
            simulation_id = str(uuid.uuid4())

            # Create simulator instance
            simulator = FocusGroupSimulator(
                personas_details=personas_details,
                stimulus_message=stimulus_message,
                stimulus_image_data=stimulus_image_data,
                moderator_questions=moderator_questions,
                open_discussion=open_discussion
            )

            # Store simulation for potential follow-up
            active_simulations[simulation_id] = simulator

            # Run simulation
            simulation_results = simulator.run_simulation(num_discussion_rounds=num_discussion_rounds)

            return jsonify({
                'simulation_id': simulation_id,
                'status': 'completed',
                'results': simulation_results
            })

        except Exception as e:
            app_logger.error(f"Error in focus group simulation: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error during simulation', 'status': 'error'}), 500

    @focus_group_bp.route('/continue/<simulation_id>', methods=['POST'])
    def continue_simulation(simulation_id):
        try:
            if simulation_id not in active_simulations:
                return jsonify({'error': 'Simulation not found', 'status': 'error'}), 404

            data = request.get_json()
            message = data.get('message', '')
            
            if not message:
                return jsonify({'error': 'Message is required', 'status': 'error'}), 400

            simulator = active_simulations[simulation_id]
            
            # Add moderator message and get responses
            responses = simulator.add_moderator_message(message)
            
            return jsonify({
                'simulation_id': simulation_id,
                'status': 'continued',
                'responses': responses
            })

        except Exception as e:
            app_logger.error(f"Error continuing simulation {simulation_id}: {e}", exc_info=True)
            return jsonify({'error': 'Error continuing simulation', 'status': 'error'}), 500

    @focus_group_bp.route('/status/<simulation_id>', methods=['GET'])
    def get_simulation_status(simulation_id):
        try:
            if simulation_id not in active_simulations:
                return jsonify({'error': 'Simulation not found', 'status': 'error'}), 404

            simulator = active_simulations[simulation_id]
            
            return jsonify({
                'simulation_id': simulation_id,
                'status': simulator.state.value,
                'current_round': simulator.current_round,
                'transcript_length': len(simulator.transcript)
            })

        except Exception as e:
            app_logger.error(f"Error getting simulation status {simulation_id}: {e}", exc_info=True)
            return jsonify({'error': 'Error getting simulation status', 'status': 'error'}), 500

    @focus_group_bp.route('/city_audiences', methods=['GET'])
    def get_city_audiences():
        """Get list of available city audiences."""
        try:
            cities = data_service.get_all_cities()
            return jsonify({'cities': cities})
        except Exception as e:
            app_logger.error(f"Error getting city audiences: {e}")
            return jsonify({'error': 'Failed to get city audiences'}), 500

    # Legacy endpoints for backward compatibility
    @focus_group_bp.route('/personas/<audience_id>', methods=['GET'])
    def get_personas_for_audience(audience_id):
        try:
            # Check if this is a city audience first
            if audience_id in ["Manchester", "Birmingham", "Liverpool", "London", "Leeds", "Newcastle", "Cardiff", "Oxford", "Norwich"]:
                city_audience = data_service.create_city_audience(audience_id)
                return jsonify({
                    'personas': city_audience['personas'],
                    'description': city_audience['description']
                })
            else:
                personas = audience_service.sample_personas_from_audience(audience_id, count=8)
                return jsonify({'personas': personas})
        except Exception as e:
            app_logger.error(f"Error getting personas for {audience_id}: {e}")
            return jsonify({'error': f'Failed to get personas for {audience_id}'}), 500

    return focus_group_bp 