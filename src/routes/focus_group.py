# src/routes/focus_group.py
from flask import Blueprint, request, jsonify
from src.services.focus_group_service import FocusGroupSimulator
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
            app_logger.info(f"Questions received in request: {questions}")
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
            # Set discussion rounds to match number of questions
            num_discussion_rounds = len(moderator_questions) if moderator_questions else 1

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

            # Run initial stimulus round if provided
            simulation_results = {
                'simulation_id': simulation_id,
                'personas': personas_details,
                'stimulus_message': stimulus_message,
                'rounds': [],
                'transcript': [],
                'summary': {}
            }
            if stimulus_message:
                stimulus_round = simulator._run_stimulus_round()
                simulation_results['rounds'].append(stimulus_round)
                simulator.transcript.extend(stimulus_round.get('responses', []))
            # Run the first moderator question round if available
            first_question_round = simulator.next_question_round()
            if first_question_round:
                simulation_results['rounds'].append(first_question_round)
                simulator.transcript.extend(first_question_round.get('responses', []))
            simulation_results['transcript'] = simulator.transcript
            # Generate analytics
            analytics = _generate_analytics(simulation_results)
            return jsonify({
                'simulation_id': simulation_id,
                'status': 'success',
                'results': simulation_results,
                'analytics': analytics
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
            simulator = active_simulations[simulation_id]
            # If a custom message is provided, treat as ad-hoc moderator question
            if message:
                responses = simulator.add_moderator_message(message)
                return jsonify({
                    'simulation_id': simulation_id,
                    'status': 'success',
                    'responses': responses
                })
            # Otherwise, progress to the next question in the queue
            next_round = simulator.next_question_round()
            if next_round:
                return jsonify({
                    'simulation_id': simulation_id,
                    'status': 'success',
                    'round': next_round
                })
            else:
                return jsonify({'simulation_id': simulation_id, 'status': 'completed', 'message': 'All questions have been asked.'})
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

    def _generate_analytics(simulation_results):
        """Generate analytics from focus group results."""
        try:
            rounds = simulation_results.get('rounds', [])
            all_responses = []
            # Collect all responses
            for round_data in rounds:
                responses = round_data.get('responses', [])
                all_responses.extend(responses)
            # Calculate basic stats
            total_responses = len(all_responses)
            total_questions = len([r for r in rounds if r.get('round_type') == 'question'])
            # Sentiment analysis
            sentiments = [r.get('sentiment', 'neutral') for r in all_responses if r.get('sentiment')]
            positive_count = len([s for s in sentiments if 'positive' in s.lower()])
            negative_count = len([s for s in sentiments if 'negative' in s.lower()])
            neutral_count = len(sentiments) - positive_count - negative_count
            sentiment_distribution = {
                'positive': round((positive_count / len(sentiments)) * 100, 1) if sentiments else 0,
                'negative': round((negative_count / len(sentiments)) * 100, 1) if sentiments else 0,
                'neutral': round((neutral_count / len(sentiments)) * 100, 1) if sentiments else 0
            }
            # Response length analysis
            response_texts = [r.get('response', '') for r in all_responses if r.get('response')]
            word_counts = [len(text.split()) for text in response_texts]
            # Extract persona names
            personas_involved = list(set([r.get('persona_description', '').split(',')[0] for r in all_responses if r.get('persona_description')]))
            # Generate key themes (basic keyword extraction)
            all_text = ' '.join(response_texts).lower()
            common_words = ['experience', 'feel', 'think', 'like', 'good', 'bad', 'better', 'important', 'value', 'quality', 'service', 'product']
            key_themes = [word for word in common_words if word in all_text][:5]
            analytics = {
                'total_responses': total_responses,
                'total_questions': total_questions,
                'sentiment_summary': {
                    'positive_responses': positive_count,
                    'negative_responses': negative_count,
                    'neutral_responses': neutral_count,
                    'sentiment_distribution': sentiment_distribution,
                    'avg_confidence': 0.85  # Placeholder
                },
                'key_themes': key_themes or ['User feedback', 'Product discussion', 'Service evaluation'],
                'personas_involved': personas_involved[:10],  # Limit to 10
                'response_lengths': {
                    'avg_words': round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
                    'longest_response': max(word_counts) if word_counts else 0,
                    'shortest_response': min(word_counts) if word_counts else 0
                }
            }
            return analytics
        except Exception as e:
            app_logger.error(f"Error generating analytics: {e}")
            return {
                'total_responses': 0,
                'total_questions': 0,
                'sentiment_summary': {'positive_responses': 0, 'negative_responses': 0, 'neutral_responses': 0},
                'key_themes': [],
                'personas_involved': [],
                'response_lengths': {'avg_words': 0, 'longest_response': 0, 'shortest_response': 0}
            }

    return focus_group_bp 