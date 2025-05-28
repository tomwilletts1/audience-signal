# src/services/persona.py
import openai
from config import config
from utils.logger import app_logger # Import logger

# Ensure OpenAI API key is configured (idempotent check)
# This relies on openai_service.py or app.py having configured it.
if not openai.api_key and config['default'].OPENAI_API_KEY:
    openai.api_key = config['default'].OPENAI_API_KEY
    app_logger.info("OpenAI API Key re-checked/set in persona service.")


def generate_persona_response(message, persona_details, model=None, temperature=None):
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
            max_tokens=config['default'].DEFAULT_MAX_TOKENS_TEXT if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_TEXT') else 300 # Add max_tokens
        )
        response_content = response.choices[0].message.content
        app_logger.info(f"Persona response generated successfully for: {persona_details[:50]}")
        return response_content
    except Exception as e:
        app_logger.error(f"OpenAI API Error in generate_persona_response for {persona_details[:50]}: {str(e)}", exc_info=True)
        if "model_not_found" in str(e):
            return "Error: The text analysis model is not available. Please try again later or contact support."
        # Consider returning a more structured error or raising an exception
        return f"Error generating persona response: {str(e)}" 