# src/services/summary.py
import openai
from config import config
from utils.logger import app_logger

if not getattr(openai, 'api_key', None) and config['default'].OPENAI_API_KEY:
    openai.api_key = config['default'].OPENAI_API_KEY
    app_logger.info("OpenAI API Key re-checked/set in summary service.")

def generate_summary_from_responses(responses_data): # Renamed 'responses' to 'responses_data'
    model = config['default'].DEFAULT_TEXT_MODEL # Summary usually uses a text model
    temperature = config['default'].DEFAULT_TEMPERATURE
    max_tokens = config['default'].DEFAULT_MAX_TOKENS_TEXT if hasattr(config['default'], 'DEFAULT_MAX_TOKENS_TEXT') else 1000 # Potentially longer for summaries
    app_logger.debug(f"Generating summary for {len(responses_data)} responses with model: {model}")

    prompt = (
        "Based on the following persona responses, provide a comprehensive summary that includes:\n"
        "1. Key themes and patterns across responses\n"
        "2. Common positive and negative feedback\n"
        "3. Specific recommendations for improvement\n"
        "4. Notable demographic-specific insights\n\n"
        "Responses:\n"
    )
    for resp_item in responses_data:
        prompt += f"\nPersona: {resp_item.get('persona', 'Unknown Persona')}\nResponse: {resp_item.get('response', 'No response text')}\n"
    
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at analyzing and summarizing consumer feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        summary_content = response.choices[0].message.content
        app_logger.info(f"Summary generated successfully for {len(responses_data)} responses.")
        return summary_content
    except Exception as e:
        app_logger.error(f"OpenAI API Error in generate_summary_from_responses: {str(e)}", exc_info=True)
        if "model_not_found" in str(e):
            return "Error: The summary generation model is not available."
        return f"Error generating summary: {str(e)}" 