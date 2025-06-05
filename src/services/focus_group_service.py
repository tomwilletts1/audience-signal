# src/services/focus_group_service.py
import openai
from enum import Enum
from typing import List
from config import config
from utils.logger import app_logger

class PersonaStyle(Enum):
    AGREEABLE = "agreeable"
    CONTRARIAN = "contrarian"
    ANALYTICAL = "analytical"
    EMOTIONAL = "emotional"
    NEUTRAL = "neutral"

class SimulationState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

class FocusGroupSimulator:
    def __init__(self, personas_details: list[str], stimulus_message: str = None, stimulus_image_data: str = None):
        if not personas_details:
            raise ValueError("At least one persona is required for a focus group.")
        if not stimulus_message and not stimulus_image_data:
            raise ValueError("A stimulus (message or image) is required.")

        self.personas_details = personas_details
        self.stimulus_message = stimulus_message
        self.stimulus_image_data = stimulus_image_data
        self.transcript = []
        self.moderator_questions = []
        self.persona_styles = {}  # Map persona_index to PersonaStyle
        self.current_round = 0
        self.state = SimulationState.RUNNING
        self.sentiment_scores = []  # Track sentiment for each response
        self.topics_identified = []  # Track emerging topics
        app_logger.info(f"FocusGroupSimulator initialized for {len(personas_details)} personas.")

    def set_persona_style(self, persona_index: int, style: PersonaStyle):
        """Set interaction style for a specific persona."""
        self.persona_styles[persona_index] = style
        app_logger.info(f"Set persona {persona_index} style to {style.value}")

    def add_moderator_question(self, question: str, after_round: int = None):
        """Add a moderator question to be asked after a specific round."""
        self.moderator_questions.append({
            'question': question,
            'after_round': after_round or self.current_round,
            'asked': False
        })
        app_logger.info(f"Added moderator question after round {after_round}: {question[:50]}...")

    def pause_simulation(self):
        """Pause the simulation."""
        self.state = SimulationState.PAUSED
        app_logger.info("Simulation paused")

    def resume_simulation(self):
        """Resume the simulation."""
        self.state = SimulationState.RUNNING
        app_logger.info("Simulation resumed")

    def inject_question(self, question: str) -> dict:
        """Inject a question mid-conversation and get immediate responses."""
        if self.state != SimulationState.RUNNING:
            raise ValueError("Cannot inject question when simulation is not running")
        
        app_logger.info(f"Injecting moderator question: {question[:50]}...")
        
        # Add moderator entry to transcript
        moderator_entry = {
            'type': 'moderator',
            'question': question,
            'round': self.current_round,
            'timestamp': self._get_timestamp()
        }
        self.transcript.append(moderator_entry)
        
        # Get responses from all personas
        responses = []
        for p_idx, p_details in enumerate(self.personas_details):
            response = self._get_llm_moderator_response(p_details, question, p_idx)
            response_entry = {
                'persona_index': p_idx,
                'persona_details': p_details,
                'response_text': response,
                'round': self.current_round,
                'type': 'moderator_response',
                'sentiment': self._analyze_sentiment(response)
            }
            self.transcript.append(response_entry)
            responses.append(response_entry)
        
        return {'moderator_question': moderator_entry, 'responses': responses}

    def _get_timestamp(self):
        """Get current timestamp for transcript entries."""
        import datetime
        return datetime.datetime.now().isoformat()

    def _get_style_prompt_modifier(self, persona_index: int) -> str:
        """Get prompt modification based on persona style."""
        style = self.persona_styles.get(persona_index, PersonaStyle.NEUTRAL)
        
        style_prompts = {
            PersonaStyle.AGREEABLE: "You tend to be agreeable and supportive, often building on others' ideas while remaining authentic to your persona.",
            PersonaStyle.CONTRARIAN: "You tend to be more questioning and critical, often presenting alternative viewpoints or playing devil's advocate while staying true to your persona.",
            PersonaStyle.ANALYTICAL: "You tend to be analytical and data-driven, asking for evidence and breaking down ideas systematically.",
            PersonaStyle.EMOTIONAL: "You tend to respond more emotionally and personally, sharing feelings and personal experiences.",
            PersonaStyle.NEUTRAL: "You respond naturally based on your persona without any particular bias toward agreement or disagreement."
        }
        
        return style_prompts[style]

    def _analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of a response using simple keyword analysis."""
        positive_words = ['good', 'great', 'excellent', 'love', 'like', 'amazing', 'wonderful', 'fantastic', 'positive', 'happy', 'excited']
        negative_words = ['bad', 'terrible', 'hate', 'dislike', 'awful', 'horrible', 'negative', 'sad', 'angry', 'frustrated', 'concerned', 'worried']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        positive_ratio = positive_count / max(total_words, 1)
        negative_ratio = negative_count / max(total_words, 1)
        
        if positive_ratio > negative_ratio:
            sentiment = "positive"
            confidence = min(positive_ratio * 10, 1.0)
        elif negative_ratio > positive_ratio:
            sentiment = "negative"
            confidence = min(negative_ratio * 10, 1.0)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_count': positive_count,
            'negative_count': negative_count
        }

    def _extract_topics(self, responses: List[str]) -> List[str]:
        """Extract main topics from responses using keyword analysis."""
        all_text = " ".join(responses).lower()
        
        # Common marketing/brand topics
        topic_keywords = {
            'price': ['price', 'cost', 'expensive', 'cheap', 'value', 'money', 'budget'],
            'quality': ['quality', 'premium', 'luxury', 'high-end', 'superior'],
            'brand': ['brand', 'reputation', 'trust', 'credibility', 'image'],
            'design': ['design', 'look', 'appearance', 'style', 'aesthetic'],
            'functionality': ['function', 'feature', 'work', 'use', 'practical'],
            'emotion': ['feel', 'emotion', 'love', 'hate', 'excited', 'worried'],
            'social': ['social', 'friends', 'family', 'community', 'share'],
            'convenience': ['convenient', 'easy', 'simple', 'quick', 'fast']
        }
        
        identified_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics

    def _analyze_consensus(self, responses: List[dict]) -> dict:
        """Analyze consensus vs disagreement in responses."""
        if len(responses) < 2:
            return {'consensus_level': 'insufficient_data', 'agreement_score': 0.0}
        
        sentiments = [r.get('sentiment', {}).get('sentiment', 'neutral') for r in responses]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        neutral_count = sentiments.count('neutral')
        
        total_responses = len(responses)
        
        # Calculate agreement score based on sentiment distribution
        if positive_count / total_responses >= 0.7:
            consensus_level = 'strong_positive'
            agreement_score = positive_count / total_responses
        elif negative_count / total_responses >= 0.7:
            consensus_level = 'strong_negative'
            agreement_score = negative_count / total_responses
        elif (positive_count + negative_count) / total_responses <= 0.3:
            consensus_level = 'neutral_consensus'
            agreement_score = neutral_count / total_responses
        else:
            consensus_level = 'mixed_opinions'
            agreement_score = 1.0 - (abs(positive_count - negative_count) / total_responses)
        
        return {
            'consensus_level': consensus_level,
            'agreement_score': agreement_score,
            'sentiment_distribution': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            }
        }

    def _get_llm_initial_reaction(self, persona_details: str, persona_index: int) -> str:
        model = config['default'].DEFAULT_TEXT_MODEL
        temperature = config['default'].DEFAULT_TEMPERATURE
        max_tokens_config_key = 'DEFAULT_MAX_TOKENS_TEXT'
        
        messages = []
        stimulus_description_for_prompt = "the provided materials"
        
        style_modifier = self._get_style_prompt_modifier(persona_index)
        
        base_prompt_text = (
            f"Persona Profile: {persona_details}\n\n"
            f"Interaction Style: {style_modifier}\n\n"
            "You are about to give your initial, independent thoughts for a focus group. "
            f"The topic is related to {stimulus_description_for_prompt}. "
            "Give yourself a name and be conversational. What are your very first, independent reactions and thoughts as this persona? "
            "Please provide only your response as the persona."
        )

        if self.stimulus_image_data:
            model = config['default'].DEFAULT_VISION_MODEL
            max_tokens_config_key = 'DEFAULT_MAX_TOKENS_VISION'
            
            content_list = [{"type": "text", "text": base_prompt_text}]
            if self.stimulus_message: 
                stimulus_description_for_prompt = f"an image and the message: \"{self.stimulus_message}\""
                base_prompt_text_updated = (
                    f"Persona Profile: {persona_details}\n\n"
                    f"Interaction Style: {style_modifier}\n\n"
                    "You are about to give your initial, independent thoughts for a focus group. "
                    f"The topic is related to an image and the message: \"{self.stimulus_message}\". "
                    "Give yourself a name and be conversational. What are your very first, independent reactions and thoughts as this persona? "
                    "Please provide only your response as the persona."
                )
                content_list = [{"type": "text", "text": base_prompt_text_updated}]

            content_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{self.stimulus_image_data}"}
            })
            messages.append({"role": "user", "content": content_list})
        
        else: 
            stimulus_description_for_prompt = f"the message: \"{self.stimulus_message}\""
            base_prompt_text_updated = (
                f"Persona Profile: {persona_details}\n\n"
                f"Interaction Style: {style_modifier}\n\n"
                "You are about to give your initial, independent thoughts for a focus group. "
                f"The topic is related to the message: \"{self.stimulus_message}\". "
                "Give yourself a name and be conversational. What are your very first, independent reactions and thoughts as this persona? "
                "Please provide only your response as the persona."
            )
            messages.append({"role": "user", "content": base_prompt_text_updated})

        max_tokens = getattr(config['default'], max_tokens_config_key, 300)
        app_logger.debug(f"Initial reaction prompt for {persona_details[:30]}... using model {model}: {str(messages)[:300]}...")

        try:
            # OpenAI client is instantiated implicitly here if OPENAI_API_KEY is in env
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            app_logger.info(f"Generated initial reaction for persona {persona_details[:30]}...")
            return content
        except Exception as e:
            app_logger.error(f"Error generating initial reaction for {persona_details[:30]}...: {str(e)}", exc_info=True)
            # Re-raise the exception to be caught by the main simulation loop
            raise

    def _get_llm_discussion_response(self, persona_details: str, conversation_history_str: str, persona_index: int) -> str:
        model = config['default'].DEFAULT_TEXT_MODEL
        temperature = config['default'].DEFAULT_TEMPERATURE
        max_tokens = getattr(config['default'], 'DEFAULT_MAX_TOKENS_TEXT', 400)

        stimulus_desc = "the previously shown materials"
        if self.stimulus_message and not self.stimulus_image_data:
            stimulus_desc = f"the message: \"{self.stimulus_message}\""
        elif self.stimulus_image_data and not self.stimulus_message:
             stimulus_desc = "the image shown earlier"
        elif self.stimulus_image_data and self.stimulus_message:
            stimulus_desc = f"the image and message: \"{self.stimulus_message}\" shown earlier"

        style_modifier = self._get_style_prompt_modifier(persona_index)

        prompt = (
            f"Persona Profile: {persona_details}\n\n"
            f"Interaction Style: {style_modifier}\n\n"
            f"You are in a focus group discussing {stimulus_desc}. "
            "Give yourself a name (if you haven't already or want to reiterate) and be conversational. "
            "Consider what has been said previously and build upon it or offer a counterpoint. Explain your reasoning.\n\n"
            "Conversation History:\n"
            f"{conversation_history_str}\n\n"
            "What are your thoughts now? Please provide only your response as this persona."
        )
        app_logger.debug(f"Discussion prompt for {persona_details[:30]}...: {prompt[:300]}...")

        try:
            # OpenAI client is instantiated implicitly here if OPENAI_API_KEY is in env
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a participant in a focus group discussion."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            app_logger.info(f"Generated discussion response for persona {persona_details[:30]}...")
            return content
        except Exception as e:
            app_logger.error(f"Error generating discussion response for {persona_details[:30]}...: {str(e)}", exc_info=True)
            # Re-raise the exception to be caught by the main simulation loop
            raise

    def _get_llm_moderator_response(self, persona_details: str, moderator_question: str, persona_index: int) -> str:
        """Generate response to a moderator question."""
        model = config['default'].DEFAULT_TEXT_MODEL
        temperature = config['default'].DEFAULT_TEMPERATURE
        max_tokens = getattr(config['default'], 'DEFAULT_MAX_TOKENS_TEXT', 400)

        style_modifier = self._get_style_prompt_modifier(persona_index)

        conversation_history_str = "\n".join([
            f"In round {t['round']}, Persona {t['persona_index']+1} said: {t['response_text']}" 
            for t in self.transcript if t.get('type') != 'moderator'
        ])

        prompt = (
            f"Persona Profile: {persona_details}\n\n"
            f"Interaction Style: {style_modifier}\n\n"
            f"You are in a focus group. The moderator has just asked: '{moderator_question}'\n\n"
            "Previous conversation context:\n"
            f"{conversation_history_str}\n\n"
            "How do you respond to the moderator's question as this persona? Be conversational and authentic."
        )

        try:
            # OpenAI client is instantiated implicitly here if OPENAI_API_KEY is in env
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are simulating a focus group participant responding to a moderator question."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            app_logger.info(f"Generated moderator response for persona {persona_details[:30]}...")
            return content
        except Exception as e:
            app_logger.error(f"Error generating moderator response for {persona_details[:30]}...: {str(e)}", exc_info=True)
            # Re-raise the exception to be caught by the main simulation loop
            raise

    def run_simulation(self, num_discussion_rounds: int = 1) -> dict:
        app_logger.info(f"Starting focus group simulation with {num_discussion_rounds} discussion round(s).")
        self.current_round = 0
        self.state = SimulationState.RUNNING
        
        try:
            # Round 0: Initial reactions
            app_logger.info("Generating initial reactions (Round 0).")
            initial_responses_current_round = []
            for p_idx, p_details in enumerate(self.personas_details):
                if self.state == SimulationState.PAUSED:
                    app_logger.info("Simulation paused during initial reactions.")
                    return self._current_simulation_status("Paused during initial reactions")

                app_logger.info(f"Generating initial reaction for persona {p_idx + 1}/{len(self.personas_details)}: {p_details[:50]}...")
                reaction = self._get_llm_initial_reaction(p_details, p_idx)
                entry = {
                    'persona_index': p_idx,
                    'persona_details': p_details,
                    'response_text': reaction,
                    'round': 0,
                    'type': 'initial_reaction',
                    'timestamp': self._get_timestamp(),
                    'sentiment': self._analyze_sentiment(reaction)
                }
                self.transcript.append(entry)
                initial_responses_current_round.append(entry)
            
            current_topics = self._extract_topics([resp['response_text'] for resp in initial_responses_current_round])
            self.topics_identified.append({'round': 0, 'topics': current_topics})

            self._check_and_ask_moderator_questions(0)

            # Discussion rounds
            for i in range(num_discussion_rounds):
                self.current_round = i + 1
                if self.state == SimulationState.PAUSED:
                    app_logger.info(f"Simulation paused before round {self.current_round}.")
                    return self._current_simulation_status(f"Paused before round {self.current_round}")
                
                app_logger.info(f"Starting discussion round {self.current_round}.")
                round_responses = [] # Store responses for this round for topic/consensus analysis

                # Build conversation history string for this round
                conversation_history_str = "\n".join([
                    f"In round {t['round']}, Persona {t['persona_index']+1} ('{t['persona_details'].split(',')[0]}') said: {t['response_text']}"
                    for t in self.transcript
                ])

                for p_idx, p_details in enumerate(self.personas_details):
                    if self.state == SimulationState.PAUSED:
                        app_logger.info(f"Simulation paused during round {self.current_round}.")
                        return self._current_simulation_status(f"Paused during round {self.current_round}")

                    app_logger.info(f"Round {self.current_round}, turn for persona {p_idx + 1}: {p_details[:50]}...")
                    response_text = self._get_llm_discussion_response(p_details, conversation_history_str, p_idx)
                    entry = {
                        'persona_index': p_idx,
                        'persona_details': p_details,
                        'response_text': response_text,
                        'round': self.current_round,
                        'type': 'discussion_response',
                        'timestamp': self._get_timestamp(),
                        'sentiment': self._analyze_sentiment(response_text)
                    }
                    self.transcript.append(entry)
                    round_responses.append(entry)
                    # Update conversation history for the next persona in the same round
                    conversation_history_str += f"\nIn round {self.current_round}, Persona {p_idx + 1} ('{p_details.split(',')[0]}') said: {response_text}"
                
                current_topics = self._extract_topics([resp['response_text'] for resp in round_responses])
                self.topics_identified.append({'round': self.current_round, 'topics': current_topics})
                self.sentiment_scores.append({'round': self.current_round, 'sentiments': [r['sentiment'] for r in round_responses]})

                self._check_and_ask_moderator_questions(self.current_round)

            self.state = SimulationState.COMPLETED
            app_logger.info(f"Focus group simulation completed. Total turns: {len(self.transcript)}")
            return {
                'status': 'completed',
                'transcript': self.transcript,
                'analytics': self._generate_analytics()
            }
        except openai.APIError as e:
            app_logger.error(f"OpenAI API Error during simulation: {str(e)}", exc_info=True)
            self.state = SimulationState.ERROR
            return {
                'status': 'error',
                'error_type': 'OpenAI API Error',
                'message': str(e),
                'transcript': self.transcript # Return partial transcript
            }
        except Exception as e:
            app_logger.error(f"Unexpected error during simulation: {str(e)}", exc_info=True)
            self.state = SimulationState.ERROR
            return {
                'status': 'error',
                'error_type': 'Unexpected Simulation Error',
                'message': str(e),
                'transcript': self.transcript # Return partial transcript
            }

    def _check_and_ask_moderator_questions(self, round_num: int):
        """Check and ask any moderator questions scheduled for this round."""
        for question_data in self.moderator_questions:
            if question_data['after_round'] == round_num and not question_data['asked']:
                try:
                    self.inject_question(question_data['question'])
                    question_data['asked'] = True
                    app_logger.info(f"Asked moderator question after round {round_num}")
                except Exception as e:
                    app_logger.error(f"Error asking moderator question: {str(e)}")

    def _generate_analytics(self) -> dict:
        """Generate comprehensive analytics for the simulation."""
        # Filter out moderator entries for analysis
        persona_responses = [t for t in self.transcript if t.get('type') != 'moderator']
        
        if not persona_responses:
            return {'error': 'No persona responses to analyze'}

        # Sentiment analysis
        sentiments = [r.get('sentiment', {}) for r in persona_responses]
        
        # Topic extraction
        response_texts = [r['response_text'] for r in persona_responses]
        topics = self._extract_topics(response_texts)
        
        # Consensus analysis
        consensus = self._analyze_consensus(persona_responses)
        
        # Round-by-round analysis
        rounds_analysis = {}
        for round_num in set(r['round'] for r in persona_responses):
            round_responses = [r for r in persona_responses if r['round'] == round_num]
            rounds_analysis[f'round_{round_num}'] = {
                'response_count': len(round_responses),
                'avg_sentiment_confidence': sum(r.get('sentiment', {}).get('confidence', 0) for r in round_responses) / len(round_responses),
                'dominant_sentiment': self._get_dominant_sentiment([r.get('sentiment', {}) for r in round_responses])
            }

        return {
            'total_responses': len(persona_responses),
            'total_rounds': max(r['round'] for r in persona_responses) + 1,
            'sentiment_summary': {
                'positive_responses': sum(1 for s in sentiments if s.get('sentiment') == 'positive'),
                'negative_responses': sum(1 for s in sentiments if s.get('sentiment') == 'negative'),
                'neutral_responses': sum(1 for s in sentiments if s.get('sentiment') == 'neutral'),
                'avg_confidence': sum(s.get('confidence', 0) for s in sentiments) / len(sentiments)
            },
            'topics_identified': topics,
            'consensus_analysis': consensus,
            'rounds_analysis': rounds_analysis,
            'persona_styles_used': {idx: style.value for idx, style in self.persona_styles.items()}
        }

    def _get_dominant_sentiment(self, sentiments: List[dict]) -> str:
        """Get the dominant sentiment from a list of sentiment analyses."""
        sentiment_counts = {}
        for s in sentiments:
            sentiment = s.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        return max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else 'neutral'

    def get_simulation_state(self) -> dict:
        """Get current simulation state and progress."""
        return {
            'state': self.state.value,
            'current_round': self.current_round,
            'total_transcript_entries': len(self.transcript),
            'moderator_questions_pending': sum(1 for q in self.moderator_questions if not q['asked']),
            'persona_count': len(self.personas_details)
        }

    def _current_simulation_status(self, message: str) -> dict:
        """Return a current simulation status dictionary with the given message."""
        return {
            'status': 'paused',
            'message': message,
            'transcript': self.transcript,
            'current_round': self.current_round
        } 