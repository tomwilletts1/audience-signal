# src/services/vision.py
import openai
from config import config
from utils.logger import app_logger

# Ensure OpenAI API key is configured
if not openai.api_key and config['default'].OPENAI_API_KEY:
    openai.api_key = config['default'].OPENAI_API_KEY
    app_logger.info("OpenAI API Key re-checked/set in vision service.")

def analyze_image(image_data, persona_details, model=None, temperature=None):
    model = model or config['default'].DEFAULT_VISION_MODEL
    temperature = temperature or config['default'].DEFAULT_TEMPERATURE
    max_tokens = config['default'].DEFAULT_MAX_TOKENS_VISION if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_VISION') else 500
    app_logger.debug(f"Analyzing image for: {persona_details[:50]} with model: {model}")

    prompt = (
        f"Persona Profile: {persona_details}\n"
        "You are a real person with this background. Give yourself a name and be conversational in response. "
        "Give your genuine reaction to this image and explain why you feel this way as if you are talking to a friend. "
        "Include specific details about what you notice and why they matter to you based on your background and values. "
        "Feel free to share personal anecdotes or experiences that relate to what you see. "
        "Be authentic and honest about both positive and negative aspects that catch your attention. "
        "Give recommendations on how you would improve the creative shown to you as if you are talking to your friend."
    )
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        response_content = response.choices[0].message.content
        app_logger.info(f"Image analysis successful for: {persona_details[:50]}")
        return response_content
    except Exception as e:
        app_logger.error(f"OpenAI API Error in analyze_image for {persona_details[:50]}: {str(e)}", exc_info=True)
        if "model_not_found" in str(e):
            return "Error: The image analysis model is not available."
        return f"Error analyzing image: {str(e)}"

def analyze_combined(image_data, message, persona_details, model=None, temperature=None):
    model = model or config['default'].DEFAULT_VISION_MODEL
    temperature = temperature or config['default'].DEFAULT_TEMPERATURE
    max_tokens = config['default'].DEFAULT_MAX_TOKENS_VISION if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_VISION') else 500
    app_logger.debug(f"Analyzing combined input for: {persona_details[:50]} with model: {model}")

    prompt = (
        f"Persona Profile: {persona_details}\n"
        f"Marketing Message: \"{message}\"\n"
        "You are a real person with this background. Give yourself a name and be conversational in response. "
        "Give your genuine reaction to both the marketing message and the image, explaining how they work together or against each other. "
        "Include specific details about what resonates with you or puts you off based on your background and values. "
        "Feel free to share personal anecdotes or experiences that relate to what you see and read. "
        "Be authentic and honest about both positive and negative aspects that catch your attention. "
        "Give recommendations on how you would improve both the message and the creative as if you are talking to your friend."
    )
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        response_content = response.choices[0].message.content
        app_logger.info(f"Combined analysis successful for: {persona_details[:50]}")
        return response_content
    except Exception as e:
        app_logger.error(f"OpenAI API Error in analyze_combined for {persona_details[:50]}: {str(e)}", exc_info=True)
        if "model_not_found" in str(e):
            return "Error: The combined analysis model is not available."
        return f"Error analyzing combined input: {str(e)}" 