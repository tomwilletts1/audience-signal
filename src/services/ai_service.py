# src/services/ai_service.py - Consolidated AI Service
import openai
import base64
from src.config import config
from src.utils.logger import app_logger

class AIService:
    """Consolidated service for all AI operations: Vision analysis and Summary generation."""
    
    def __init__(self):
        # Ensure OpenAI API key is configured
        if not openai.api_key and config['default'].OPENAI_API_KEY:
            openai.api_key = config['default'].OPENAI_API_KEY
        app_logger.info("AIService initialized for vision and summary operations.")

    # ==================== VISION ANALYSIS ====================
    def analyze_image(self, image_data, persona_details, model=None, temperature=None):
        """Analyze an image from a specific persona's perspective."""
        model = model or config['default'].DEFAULT_VISION_MODEL
        temperature = temperature or config['default'].DEFAULT_TEMPERATURE
        
        app_logger.debug(f"Analyzing image for persona: {persona_details[:50]}... with model: {model}")
        
        # Extract persona name for response consistency
        persona_name = persona_details.split(',')[0].strip()
        name_enforcement = config['default'].PERSONA_NAME_ENFORCEMENT_PROMPT.format(name=persona_name)
        
        prompt = (
            f"Persona Profile: {persona_details}\n"
            f"{name_enforcement}\n\n"
            "You are this persona looking at this image. Give your genuine reaction and thoughts. "
            "What catches your attention? What do you think about it based on your background and values? "
            "Be authentic and conversational as if talking to a friend."
        )
        
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": prompt
                    }, {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }]
                }],
                temperature=temperature,
                max_tokens=config['default'].DEFAULT_MAX_TOKENS_VISION if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_VISION') else 300
            )
            
            result = response.choices[0].message.content
            app_logger.info(f"Image analysis completed for persona: {persona_details[:50]}...")
            return result
            
        except Exception as e:
            app_logger.error(f"Error in image analysis for {persona_details[:50]}...: {str(e)}", exc_info=True)
            if "model_not_found" in str(e):
                return "Error: The vision model is not available. Please try again later."
            return f"Error analyzing image: {str(e)}"

    def analyze_combined(self, image_data, message, persona_details, model=None, temperature=None):
        """Analyze both image and text message from persona's perspective."""
        model = model or config['default'].DEFAULT_VISION_MODEL
        temperature = temperature or config['default'].DEFAULT_TEMPERATURE
        
        app_logger.debug(f"Analyzing combined content for persona: {persona_details[:50]}...")
        
        # Extract persona name
        persona_name = persona_details.split(',')[0].strip()
        name_enforcement = config['default'].PERSONA_NAME_ENFORCEMENT_PROMPT.format(name=persona_name)
        
        prompt = (
            f"Persona Profile: {persona_details}\n"
            f"{name_enforcement}\n\n"
            f"You are viewing an image along with this message: \"{message}\"\n\n"
            "As this persona, give your reaction to both the image and the message together. "
            "How do they work together? What's your overall impression? "
            "Be authentic and conversational."
        )
        
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": prompt
                    }, {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }]
                }],
                temperature=temperature,
                max_tokens=config['default'].DEFAULT_MAX_TOKENS_VISION if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_VISION') else 400
            )
            
            result = response.choices[0].message.content
            app_logger.info(f"Combined analysis completed for persona: {persona_details[:50]}...")
            return result
            
        except Exception as e:
            app_logger.error(f"Error in combined analysis for {persona_details[:50]}...: {str(e)}", exc_info=True)
            return f"Error analyzing combined content: {str(e)}"

    # ==================== SUMMARY GENERATION ====================
    def generate_summary_from_responses(self, responses_data):
        """Generate a comprehensive summary from focus group responses."""
        model = config['default'].DEFAULT_TEXT_MODEL
        temperature = config['default'].DEFAULT_TEMPERATURE
        
        app_logger.debug(f"Generating summary from {len(responses_data)} responses")
        
        # Prepare responses text
        responses_text = ""
        for i, response in enumerate(responses_data, 1):
            persona_info = response.get('persona', 'Unknown')
            content = response.get('content', '')
            responses_text += f"Response {i} ({persona_info}): {content}\n\n"
        
        prompt = (
            "You are an expert market researcher analyzing focus group responses. "
            "Please provide a comprehensive summary of the following responses:\n\n"
            f"{responses_text}\n\n"
            "Your summary should include:\n"
            "1. Key themes and common patterns\n"
            "2. Notable differences in opinions\n"
            "3. Actionable insights for marketers\n"
            "4. Overall sentiment analysis\n\n"
            "Be concise but thorough, focusing on practical insights."
        )
        
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[{
                    "role": "system",
                    "content": "You are an expert market research analyst specializing in focus group analysis."
                }, {
                    "role": "user", 
                    "content": prompt
                }],
                temperature=temperature,
                max_tokens=config['default'].DEFAULT_MAX_TOKENS_TEXT if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_TEXT') else 800
            )
            
            summary = response.choices[0].message.content
            app_logger.info(f"Summary generated successfully from {len(responses_data)} responses")
            return summary
            
        except Exception as e:
            app_logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            if "model_not_found" in str(e):
                return "Error: The text analysis model is not available. Please try again later."
            return f"Error generating summary: {str(e)}"

    def generate_persona_response(self, message, persona_details, model=None, temperature=None):
        """Generate a persona response to a marketing message."""
        model = model or config['default'].DEFAULT_TEXT_MODEL
        temperature = temperature or config['default'].DEFAULT_TEMPERATURE
        app_logger.debug(f"Generating persona response for: {persona_details[:50]} with model: {model}")

        prompt = (
            f"Persona Profile: {persona_details}\n"
            f"Marketing Message: \"{message}\"\n"
            "You are a real person with this background. Give yourself a name and be conversational in response. "
            "Give your genuine reaction to this marketing message and explain why you feel this way as if you are talking to a friend. "
            "Include specific details about what resonates with you or puts you off based on your background and values. "
            "Feel free to share personal anecdotes or experiences that relate to the message. "
            "Be authentic and honest about both positive and negative aspects that catch your attention. "
            "Give recommendations on how you would improve the message as if you are talking to your friend."
        )
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a consumer simulator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=config['default'].DEFAULT_MAX_TOKENS_TEXT if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_TEXT') else 300
            )
            response_content = response.choices[0].message.content
            app_logger.info(f"Persona response generated successfully for: {persona_details[:50]}")
            return response_content
        except Exception as e:
            app_logger.error(f"OpenAI API Error in generate_persona_response for {persona_details[:50]}: {str(e)}", exc_info=True)
            if "model_not_found" in str(e):
                return "Error: The text analysis model is not available. Please try again later or contact support."
            return f"Error generating persona response: {str(e)}" 