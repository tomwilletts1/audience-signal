import openai
from config import config
from utils.logger import app_logger

# Configure OpenAI API Key
# The openai library (v1.x+) will automatically pick up OPENAI_API_KEY from the environment.
# The explicit assignment `openai.api_key = ...` is generally for older versions or specific client instances.
# We ensure .env is loaded by config.py, which sets the environment variable.

loaded_api_key = config['default'].OPENAI_API_KEY
if loaded_api_key:
    # No longer setting openai.api_key directly on the module here.
    # The library will use the environment variable OPENAI_API_KEY.
    app_logger.info("OPENAI_API_KEY is present in configuration and environment.")
else:
    app_logger.warning("OPENAI_API_KEY not found in configuration. OpenAI services might not work if not set elsewhere in environment.")

# This file now primarily handles OpenAI API key configuration.
# Other general OpenAI related utility functions that don't fit into
# more specific services (persona, vision, summary) could reside here if needed in the future.

# Note: The analyze_image function below uses openai.Image.create, 
# which is for openai < v1.0. It will need to be updated to use the new API structure, e.g.,
# client = openai.OpenAI() (client will auto-load key from env)
# response = client.images.generate(...)
# This is outside the scope of the current API key loading fix for focus groups.

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
        app_logger.error(f"OpenAI API Error: {str(e)}")
        if "model_not_found" in str(e):
            return "Error: The image analysis model is not available. Please try again later or contact support."
        return f"Error analyzing image: {str(e)}"
