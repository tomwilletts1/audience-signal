# src/services/focus_group_service.py
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from src.services.ai_service import AIService
from src.utils.logger import app_logger

class SimulationState(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

class FocusGroupSimulator:
    """
    Focus Group Simulator that accepts personas and runs interactive simulations.
    
    This simulator takes pre-built personas and runs focus group discussions,
    allowing for interactive moderator questions and open discussions.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the focus group simulator with backward compatibility.
        
        Two calling patterns supported:
        1. NEW: FocusGroupSimulator(personas_details=..., stimulus_message=..., ...)
        2. OLD: FocusGroupSimulator(data_service, ai_service)
        
        Args:
            For NEW pattern:
                personas_details: List of persona dictionaries with demographics and descriptions
                stimulus_message: Initial message or topic to discuss
                stimulus_image_data: Optional image data for visual stimulus
                moderator_questions: List of questions for the moderator to ask
                open_discussion: Whether to allow open discussion between participants
            
            For OLD pattern:
                data_service: DataService instance
                ai_service: AIService instance
        """
        # Detect calling pattern
        if len(args) == 2 and len(kwargs) == 0:
            # Old pattern: FocusGroupSimulator(data_service, ai_service)
            data_service, ai_service = args
            self._init_old_pattern(data_service, ai_service)
        else:
            # New pattern: FocusGroupSimulator(personas_details=..., ...)
            personas_details = args[0] if args else kwargs.get('personas_details', [])
            stimulus_message = kwargs.get('stimulus_message')
            stimulus_image_data = kwargs.get('stimulus_image_data')
            moderator_questions = kwargs.get('moderator_questions', [])
            open_discussion = kwargs.get('open_discussion', False)
            self._init_new_pattern(personas_details, stimulus_message, stimulus_image_data, 
                                 moderator_questions, open_discussion)
    
    def _init_old_pattern(self, data_service, ai_service):
        """Initialize using the old hybrid pattern."""
        from src.services.hybrid_audience_service import HybridAudienceService
        
        self.data_service = data_service
        self.ai_service = ai_service
        self.hybrid_service = HybridAudienceService(data_service, ai_service)
        self.active_simulations = {}
        
        # Set default values for new pattern attributes
        self.personas_details = []
        self.stimulus_message = ""
        self.stimulus_image_data = None
        self.moderator_questions = []
        self.open_discussion = False
        self.state = SimulationState.INITIALIZING
        self.current_round = 0
        self.transcript = []
        self.simulation_id = str(uuid.uuid4())
        
        app_logger.info("FocusGroupSimulator initialized with hybrid services (old pattern)")
    
    def _init_new_pattern(self, personas_details, stimulus_message, stimulus_image_data, 
                         moderator_questions, open_discussion):
        """Initialize using the new direct pattern."""
        self.personas_details = personas_details or []
        self.stimulus_message = stimulus_message or ""
        self.stimulus_image_data = stimulus_image_data
        self.moderator_questions = moderator_questions or []
        self.open_discussion = open_discussion
        
        # Simulation state
        self.state = SimulationState.INITIALIZING
        self.current_round = 0
        self.transcript = []
        self.simulation_id = str(uuid.uuid4())
        self.current_question_index = 0  # Track which moderator question is next
        
        # Initialize AI service for generating responses
        self.ai_service = AIService()
        
        # Set None for old pattern attributes
        self.data_service = None
        self.hybrid_service = None
        self.active_simulations = None
        
        app_logger.info(f"Initialized FocusGroupSimulator with {len(self.personas_details)} personas (new pattern)")
        
    def run_simulation(self, num_discussion_rounds=None):
        """
        Run the complete focus group simulation.
        Args:
            num_discussion_rounds: Number of discussion rounds to run (if None, use all moderator questions)
        Returns:
            Dict with simulation results
        """
        try:
            self.state = SimulationState.ACTIVE
            app_logger.info(f"Starting focus group simulation with {len(self.personas_details)} personas")
            app_logger.info(f"Moderator questions received: {self.moderator_questions}")

            results = {
                'simulation_id': self.simulation_id,
                'personas': self.personas_details,
                'stimulus_message': self.stimulus_message,
                'rounds': [],
                'transcript': [],
                'summary': {}
            }

            # Initial stimulus round if provided
            if self.stimulus_message:
                stimulus_round = self._run_stimulus_round()
                results['rounds'].append(stimulus_round)
                self.transcript.extend(stimulus_round.get('responses', []))

            # Always use all moderator questions if present
            questions_to_ask = self.moderator_questions if self.moderator_questions else []
            for i, question in enumerate(questions_to_ask):
                question_round = self._run_question_round(question, i + 1)
                results['rounds'].append(question_round)
                self.transcript.extend(question_round.get('responses', []))
                self.current_round += 1

            # Generate simulation summary
            results['summary'] = self._generate_simulation_summary()
            results['transcript'] = self.transcript

            self.state = SimulationState.COMPLETED
            app_logger.info(f"Completed focus group simulation {self.simulation_id}")

            return results

        except Exception as e:
            self.state = SimulationState.ERROR
            app_logger.error(f"Error in focus group simulation: {e}", exc_info=True)
            raise
    
    def add_moderator_message(self, message):
        """
        Add a moderator message and get responses from all personas.
        
        Args:
            message: Moderator message/question
            
        Returns:
            List of persona responses
        """
        try:
            app_logger.info(f"Adding moderator message: {message}")
            
            responses = []
            for persona in self.personas_details:
                response = self._generate_persona_response(persona, message)
                responses.append(response)
                
            # Add to transcript
            moderator_entry = {
                'type': 'moderator',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            self.transcript.append(moderator_entry)
            
            # Add responses to transcript
            for response in responses:
                self.transcript.append({
                    'type': 'participant',
                    'persona_id': response['persona_id'],
                    'message': response['response'],
                    'timestamp': datetime.now().isoformat()
                })
            
            return responses
            
        except Exception as e:
            app_logger.error(f"Error adding moderator message: {e}", exc_info=True)
            raise
    
    def _run_stimulus_round(self):
        """Run the initial stimulus round."""
        app_logger.info("Running stimulus round")
        
        responses = []
        for persona in self.personas_details:
            response = self._generate_persona_response(persona, self.stimulus_message, is_stimulus=True)
            responses.append(response)
        
        return {
            'round_type': 'stimulus',
            'stimulus': self.stimulus_message,
            'responses': responses,
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_question_round(self, question, round_number):
        """Run a moderator question round."""
        app_logger.info(f"Running question round {round_number}: {question}")
        
        responses = []
        for persona in self.personas_details:
            response = self._generate_persona_response(persona, question)
            responses.append(response)
        
        return {
            'round_type': 'question',
            'round_number': round_number,
            'question': question,
            'responses': responses,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_persona_response(self, persona, message, is_stimulus=False):
        """
        Generate a response from a specific persona to a message.
        
        Args:
            persona: Persona dictionary with demographics/description OR string description
            message: Message to respond to
            is_stimulus: Whether this is a stimulus response
            
        Returns:
            Dict with persona response
        """
        try:
            # Handle both string personas (from city audiences) and dict personas (from other sources)
            if isinstance(persona, str):
                # String persona from city audience
                persona_id = f"participant_{len(self.transcript) + 1}"
                persona_description = persona
                demographics = self._parse_string_persona(persona)
            else:
                # Dictionary persona from other sources
                persona_id = persona.get('id', f"participant_{len(self.transcript) + 1}")
                demographics = persona.get('demographics', {})
                persona_description = persona.get('description', 'A focus group participant')
            
            # Build context for AI response
            if isinstance(persona, str):
                # For string personas, use the full description as context
                context = f"""
                You are a focus group participant: {persona_description}
                
                {"This is your initial reaction to the stimulus:" if is_stimulus else "Please respond to this question:"}
                "{message}"
                
                Respond naturally as this person would, considering their background and characteristics.
                Keep your response conversational and authentic (2-4 sentences).
                """
            else:
                # For dict personas, use structured demographics
                context = f"""
                You are a focus group participant with the following characteristics:
                
                Demographics:
                - Age: {demographics.get('age', 'Unknown')}
                - Occupation: {demographics.get('occupation', 'Unknown')}
                - Income: {demographics.get('income', 'Unknown')}
                - Region: {demographics.get('region', 'Unknown')}
                
                Description: {persona_description}
                
                {"This is your initial reaction to the stimulus:" if is_stimulus else "Please respond to this question:"}
                "{message}"
                
                Respond naturally as this person would, considering their background and characteristics.
                Keep your response conversational and authentic (2-4 sentences).
                """
            
            # Generate response using AI service - use focus group specific method
            if isinstance(persona, str):
                persona_context = persona
            else:
                # Build context from persona dict
                demographics = persona.get('demographics', {})
                description = persona.get('description', 'A focus group participant')
                persona_context = f"{description}\nAge: {demographics.get('age', 'Unknown')}, Occupation: {demographics.get('occupation', 'Unknown')}, Region: {demographics.get('region', 'Unknown')}"
            
            ai_response = self.ai_service.generate_focus_group_response(
                question=message,  # Pass the actual question directly
                persona_details=persona_context,
                temperature=0.8
            )
            
            response_text = ai_response if ai_response else 'I have no comment on this.'
            
            return {
                'persona_id': persona_id,
                'persona_description': persona_description,
                'demographics': demographics,
                'response': response_text,
                'sentiment': self._analyze_sentiment(response_text),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            app_logger.error(f"Error generating persona response: {e}", exc_info=True)
            fallback_id = persona.get('id', 'unknown') if isinstance(persona, dict) else 'unknown'
            return {
                'persona_id': fallback_id,
                'response': 'I prefer not to comment.',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_string_persona(self, persona_str):
        """
        Parse a string persona into demographics dict.
        
        Args:
            persona_str: String like "Sarah Mitchell, 32, Digital Marketing Manager, Manchester city centre, ..."
            
        Returns:
            Dict with extracted demographics
        """
        try:
            # Split the string and try to extract key info
            parts = persona_str.split(', ')
            
            demographics = {}
            
            # Try to extract name (first part)
            if len(parts) > 0:
                demographics['name'] = parts[0]
            
            # Try to extract age (second part, if it's a number)
            if len(parts) > 1:
                try:
                    age = int(parts[1])
                    demographics['age'] = age
                except ValueError:
                    pass
            
            # Try to extract occupation (third part)
            if len(parts) > 2:
                demographics['occupation'] = parts[2]
            
            # Try to extract location (fourth part)
            if len(parts) > 3:
                demographics['region'] = parts[3]
            
            # Try to extract other info from remaining parts
            for part in parts[4:]:
                if '£' in part and ('pay' in part.lower() or 'income' in part.lower()):
                    # Extract income info
                    demographics['income_info'] = part
                elif '%' in part:
                    # Some percentage-based metric
                    demographics['engagement_info'] = part
            
            return demographics
            
        except Exception as e:
            app_logger.error(f"Error parsing string persona: {e}")
            return {'description': persona_str}
    
    def _analyze_sentiment(self, text):
        """Basic sentiment analysis of response text."""
        positive_words = ['good', 'great', 'excellent', 'love', 'like', 'positive', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'hate', 'dislike', 'negative', 'awful', 'horrible', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _generate_simulation_summary(self):
        """Generate a summary of the simulation results."""
        try:
            total_responses = len([entry for entry in self.transcript if entry.get('type') == 'participant'])
            
            # Analyze sentiment distribution
            sentiments = [self._analyze_sentiment(entry.get('message', '')) 
                         for entry in self.transcript if entry.get('type') == 'participant']
            
            sentiment_counts = {
                'positive': sentiments.count('positive'),
                'neutral': sentiments.count('neutral'),
                'negative': sentiments.count('negative')
            }
            
            return {
                'total_participants': len(self.personas_details),
                'total_responses': total_responses,
                'rounds_completed': self.current_round,
                'sentiment_distribution': sentiment_counts,
                'simulation_duration': len(self.transcript),
                'key_themes': self._extract_key_themes(),
                'completion_status': self.state.value
            }
            
        except Exception as e:
            app_logger.error(f"Error generating simulation summary: {e}", exc_info=True)
            return {'error': 'Could not generate summary'}
    
    def _extract_key_themes(self):
        """Extract key themes from the discussion."""
        # Simple keyword extraction - could be enhanced with NLP
        participant_messages = [entry.get('message', '') for entry in self.transcript 
                              if entry.get('type') == 'participant']
        
        if not participant_messages:
            return []
        
        # Combine all messages and extract common themes
        all_text = ' '.join(participant_messages).lower()
        
        # Simple theme extraction based on common words
        common_themes = []
        if 'price' in all_text or 'cost' in all_text or 'expensive' in all_text:
            common_themes.append('pricing_concerns')
        if 'quality' in all_text or 'good' in all_text or 'bad' in all_text:
            common_themes.append('quality_discussion')
        if 'experience' in all_text or 'service' in all_text:
            common_themes.append('experience_feedback')
        
        return common_themes[:5]  # Return top 5 themes 

    def next_question_round(self):
        """
        Progress to the next moderator question and return persona responses.
        Returns None if no more questions remain.
        """
        if self.current_question_index >= len(self.moderator_questions):
            return None  # No more questions
        question = self.moderator_questions[self.current_question_index]
        self.current_question_index += 1
        round_number = self.current_question_index
        question_round = self._run_question_round(question, round_number)
        self.transcript.extend(question_round.get('responses', []))
        self.current_round += 1
        return question_round

    # === OLD PATTERN COMPATIBILITY METHODS ===
    # These methods maintain backward compatibility with the hybrid demo and other files
    
    def start_simulation(self, config: Dict) -> str:
        """
        Start a focus group simulation with enhanced hybrid personas (OLD PATTERN).
        
        Args:
            config: Simulation configuration including city, group size, questions
            
        Returns:
            Simulation ID
        """
        if not hasattr(self, 'hybrid_service') or self.hybrid_service is None:
            raise RuntimeError("start_simulation requires FocusGroupSimulator to be initialized with data_service and ai_service")
            
        try:
            simulation_id = str(uuid.uuid4())
            
            # Extract configuration
            city = config.get('city', 'Manchester')
            group_size = min(int(config.get('group_size', 6)), 10)  # Cap at 10
            questions = config.get('questions', [])
            product_context = config.get('product_context', '')
            
            # Step 1: Create enhanced personas using hybrid approach
            app_logger.info(f"Creating {group_size} enhanced personas for {city}")
            personas = []
            
            for i in range(group_size):
                enhanced_persona = self.hybrid_service.create_enhanced_persona(
                    city=city,
                    persona_criteria=config.get('persona_criteria', {})
                )
                
                # Add persona to group with unique identifier
                enhanced_persona['group_id'] = f"participant_{i+1}"
                enhanced_persona['simulation_id'] = simulation_id
                personas.append(enhanced_persona)
            
            # Step 2: Initialize simulation state
            simulation_state = {
                'id': simulation_id,
                'city': city,
                'config': config,
                'personas': personas,
                'questions': questions,
                'current_question_index': 0,
                'responses': [],
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'data_layers': {
                    'sqlite_foundation': True,
                    'chromadb_enhancement': True,
                    'ai_generation': True
                }
            }
            
            self.active_simulations[simulation_id] = simulation_state
            
            app_logger.info(f"Started hybrid focus group simulation {simulation_id} for {city} with {group_size} personas")
            return simulation_id
            
        except Exception as e:
            app_logger.error(f"Error starting simulation: {e}", exc_info=True)
            raise
    
    def process_question(self, simulation_id: str, question: str = None) -> Dict:
        """
        Process a question using hybrid personas with rich context (OLD PATTERN).
        
        Args:
            simulation_id: Active simulation ID
            question: Question to ask (optional, will use next in queue)
            
        Returns:
            Responses from all personas with enhanced context
        """
        if not hasattr(self, 'hybrid_service') or self.hybrid_service is None:
            raise RuntimeError("process_question requires FocusGroupSimulator to be initialized with data_service and ai_service")
            
        try:
            if simulation_id not in self.active_simulations:
                raise ValueError(f"Simulation {simulation_id} not found")
            
            simulation = self.active_simulations[simulation_id]
            
            # Determine question to ask
            if question is None:
                questions = simulation['questions']
                current_index = simulation['current_question_index']
                
                if current_index >= len(questions):
                    return {'status': 'completed', 'message': 'All questions have been answered'}
                
                question = questions[current_index]
                simulation['current_question_index'] += 1
            
            app_logger.info(f"Processing question for simulation {simulation_id}: {question}")
            
            # Generate responses from all personas using hybrid approach
            persona_responses = []
            
            for persona in simulation['personas']:
                # Use hybrid service for contextually rich responses
                response = self.hybrid_service.generate_contextual_focus_group_response(
                    persona=persona,
                    question=question,
                    product_context=simulation['config'].get('product_context', '')
                )
                
                # Add simulation metadata
                response_data = {
                    'persona_id': persona['group_id'],
                    'persona_description': persona.get('ai_description', 'Enhanced hybrid persona'),
                    'question': question,
                    'response': response.get('content', ''),
                    'sentiment': response.get('sentiment', 'neutral'),
                    'reasoning': response.get('reasoning', ''),
                    'context_quality': response.get('context_quality', 'medium'),
                    'data_sources': persona.get('data_sources', {}),
                    'timestamp': datetime.now().isoformat(),
                    'chromadb_response_id': response.get('chromadb_id'),
                    'demographic_foundation': {
                        'city': persona.get('demographics', {}).get('region', simulation['city']),
                        'age': persona.get('demographics', {}).get('age'),
                        'occupation': persona.get('demographics', {}).get('occupation'),
                        'income': persona.get('demographics', {}).get('income')
                    }
                }
                
                persona_responses.append(response_data)
            
            # Store responses in simulation
            question_session = {
                'question': question,
                'responses': persona_responses,
                'asked_at': datetime.now().isoformat(),
                'session_summary': self._generate_session_summary_old(persona_responses)
            }
            
            simulation['responses'].append(question_session)
            
            return {
                'status': 'success',
                'simulation_id': simulation_id,
                'question': question,
                'responses': persona_responses,
                'session_summary': question_session['session_summary'],
                'progress': {
                    'current_question': simulation['current_question_index'],
                    'total_questions': len(simulation['questions']),
                    'completed': simulation['current_question_index'] >= len(simulation['questions'])
                },
                'data_quality': self._assess_response_quality_old(persona_responses)
            }
            
        except Exception as e:
            app_logger.error(f"Error processing question: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def get_simulation_insights(self, simulation_id: str) -> Dict:
        """
        Get comprehensive insights from the simulation using hybrid data analysis (OLD PATTERN).
        """
        if not hasattr(self, 'active_simulations') or self.active_simulations is None:
            raise RuntimeError("get_simulation_insights requires FocusGroupSimulator to be initialized with data_service and ai_service")
            
        if simulation_id not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        simulation = self.active_simulations[simulation_id]
        return {
            'simulation_id': simulation_id,
            'city': simulation['city'],
            'status': 'insights_generated',
            'message': 'Hybrid insights available (old pattern compatibility)'
        }
    
    def _generate_session_summary_old(self, responses: List[Dict]) -> Dict:
        """Generate summary of responses for a question session (OLD PATTERN)."""
        if not responses:
            return {'themes': [], 'sentiment_distribution': {}, 'key_quotes': []}
        
        # Extract themes and sentiments
        themes = []
        sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
        key_quotes = []
        
        for response in responses:
            sentiment = response.get('sentiment', 'neutral')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Extract potential themes from reasoning
            reasoning = response.get('reasoning', '')
            if reasoning and len(reasoning) > 20:
                themes.append(reasoning[:100] + '...' if len(reasoning) > 100 else reasoning)
            
            # Collect interesting quotes
            response_text = response.get('response', '')
            if len(response_text) > 50:
                key_quotes.append({
                    'persona': response.get('persona_id'),
                    'quote': response_text[:150] + '...' if len(response_text) > 150 else response_text
                })
        
        return {
            'themes': themes[:5],  # Top 5 themes
            'sentiment_distribution': sentiments,
            'key_quotes': key_quotes[:3],  # Top 3 quotes
            'response_count': len(responses)
        }
    
    def _assess_response_quality_old(self, responses: List[Dict]) -> Dict:
        """Assess the quality of generated responses (OLD PATTERN)."""
        if not responses:
            return {'overall': 'low', 'details': 'No responses generated'}
        
        quality_indicators = {
            'context_quality_high': 0,
            'demographic_foundation': 0,
            'chromadb_enhanced': 0,
            'reasoning_provided': 0
        }
        
        for response in responses:
            if response.get('context_quality') == 'high':
                quality_indicators['context_quality_high'] += 1
            
            if response.get('demographic_foundation'):
                quality_indicators['demographic_foundation'] += 1
            
            if response.get('chromadb_response_id'):
                quality_indicators['chromadb_enhanced'] += 1
            
            if response.get('reasoning'):
                quality_indicators['reasoning_provided'] += 1
        
        total_responses = len(responses)
        quality_score = sum(quality_indicators.values()) / (total_responses * 4)  # 4 indicators
        
        if quality_score >= 0.8:
            overall = 'high'
        elif quality_score >= 0.5:
            overall = 'medium'
        else:
            overall = 'low'
        
        return {
            'overall': overall,
            'score': quality_score,
            'indicators': quality_indicators,
            'details': f"{quality_indicators['context_quality_high']}/{total_responses} high-quality context responses"
        } 