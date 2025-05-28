import openai
from config import config
from utils.logger import app_logger

# Configure OpenAI API Key
# This should be one of the first things to run, so services can rely on it.
api_key = config['default'].OPENAI_API_KEY
if api_key:
    openai.api_key = api_key
    app_logger.info("OpenAI API Key configured from openai_service.")
else:
    app_logger.warning("OPENAI_API_KEY not found in configuration. OpenAI services might not work.")

# This file now primarily handles OpenAI API key configuration.
# Other general OpenAI related utility functions that don't fit into
# more specific services (persona, vision, summary) could reside here if needed in the future.

def analyze_image(image_data, persona_details, model=config['default'].DEFAULT_VISION_MODEL, temperature=config['default'].DEFAULT_TEMPERATURE):
    try:
        response = openai.Image.create(
            model=model,
            prompt=f"Persona Profile: {persona_details}\nMarketing Message: \"{image_data}\"\nYou are a real person with this background. Give yourself a name and be conversational in response. Give your genuine reaction to this marketing message and explain why you feel this way as if you are talking to a friend. Include specific details about what resonates with you or puts you off based on your background and values. Feel free to share personal anecdotes or experiences that relate to the message. Be authentic and honest about both positive and negative aspects that catch your attention. Give recommendations on how you would improve the message as if you are talking to your friend.",
            n=1,
            size="256x256"
        )
        return response['data'][0]['url']
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        if "model_not_found" in str(e):
            return "Error: The image analysis model is not available. Please try again later or contact support."
        return f"Error analyzing image: {str(e)}"

def analyze_combined(image_data, message, persona_details, model=config['default'].DEFAULT_VISION_MODEL, temperature=config['default'].DEFAULT_TEMPERATURE):
    # This function is now removed from this file.
    # It has been moved to src/services/persona.py
    pass 