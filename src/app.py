from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
import os
from datetime import datetime
from config import config

# Initialize Flask app with configuration
app = Flask(__name__, static_folder=config['default'].FRONTEND_DIR)
CORS(app, resources={r"/api/*": {"origins": config['default'].CORS_ORIGINS}})

# Configure OpenAI
openai.api_key = config['default'].OPENAI_API_KEY

# In-memory storage for response history
response_history = []

def analyze_image(image_data, persona_details, model=config['default'].DEFAULT_VISION_MODEL, temperature=config['default'].DEFAULT_TEMPERATURE):
    """
    Analyze an image using GPT-4 Vision and generate a persona's reaction.
    """
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
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]}
            ],
            max_tokens=500,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        if "model_not_found" in str(e):
            return "Error: The image analysis model is not available. Please try again later or contact support."
        return f"Error analyzing image: {str(e)}"

def generate_persona_response(message, persona_details, model=config['default'].DEFAULT_TEXT_MODEL, temperature=config['default'].DEFAULT_TEMPERATURE):
    """
    Generate a response from a synthetic persona based on a marketing message.
    """
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
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        if "model_not_found" in str(e):
            return "Error: The text analysis model is not available. Please try again later or contact support."
        return f"Error generating response: {str(e)}"

def generate_summary(responses):
    """
    Generate a summary of all persona responses.
    """
    prompt = (
        "Based on the following persona responses, provide a comprehensive summary that includes:\n"
        "1. Key themes and patterns across responses\n"
        "2. Common positive and negative feedback\n"
        "3. Specific recommendations for improvement\n"
        "4. Notable demographic-specific insights\n\n"
        "Responses:\n"
    )
    
    for response in responses:
        prompt += f"\nPersona: {response['persona']}\nResponse: {response['response']}\n"
    
    try:
        response = openai.chat.completions.create(
            model=config['default'].DEFAULT_TEXT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at analyzing and summarizing consumer feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=config['default'].DEFAULT_TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return f"Error generating summary: {str(e)}"

def analyze_combined(image_data, message, persona_details, model=config['default'].DEFAULT_VISION_MODEL, temperature=config['default'].DEFAULT_TEMPERATURE):
    """
    Analyze both an image and marketing message together using GPT-4 Vision and generate a persona's reaction.
    """
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
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]}
            ],
            max_tokens=500,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        if "model_not_found" in str(e):
            return "Error: The combined analysis model is not available. Please try again later or contact support."
        return f"Error analyzing combined input: {str(e)}"

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/analyze', methods=['POST'])
def analyze_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400

        message = data.get('message')
        personas = data.get('personas', [])
        image_data = data.get('image')
        
        if not personas:
            return jsonify({
                'error': 'Personas are required',
                'status': 'error'
            }), 400
        
        if not message and not image_data:
            return jsonify({
                'error': 'Either message or image is required',
                'status': 'error'
            }), 400
        
        results = []
        for persona in personas:
            if image_data and message:
                response = analyze_combined(image_data, message, persona)
            elif image_data:
                response = analyze_image(image_data, persona)
            else:
                response = generate_persona_response(message, persona)
            
            results.append({
                'persona': persona,
                'response': response
            })
        
        # Store in history
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'image': bool(image_data),
            'personas': personas,
            'results': results
        }
        response_history.append(history_entry)
        
        return jsonify({
            'results': results,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"Error in analyze_message: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        return jsonify(response_history)
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/summary', methods=['POST'])
def generate_response_summary():
    try:
        data = request.get_json()
        if not data or 'responses' not in data:
            return jsonify({
                'error': 'No responses provided',
                'status': 'error'
            }), 400

        summary = generate_summary(data['responses'])
        return jsonify({
            'summary': summary,
            'status': 'success'
        })
    except Exception as e:
        print(f"Error in generate_response_summary: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/presets', methods=['GET'])
def get_presets():
    try:
        return jsonify({
            'status': 'success',
            'presets': config['default'].PERSONA_PRESETS
        })
    except Exception as e:
        print(f"Error in get_presets: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(
        debug=config['default'].DEBUG,
        host=config['default'].HOST,
        port=config['default'].PORT
    ) 