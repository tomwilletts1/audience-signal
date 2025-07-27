import os
from dotenv import load_dotenv

# Determine the absolute path to the .env file in the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env.txt')

# Load environment variables
# Explicitly load the .env.txt file from the project root
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    # This case should ideally log a warning if .env.txt is expected
    pass

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Application Configuration
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # CORS Configuration
    CORS_ORIGINS = ['*']  # In production, replace with specific origins
    
    # File Paths
    FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    
    # Model Configuration
    DEFAULT_TEXT_MODEL = "gpt-4o"
    DEFAULT_VISION_MODEL = "gpt-4-vision-preview"
    DEFAULT_TEMPERATURE = 0.7
    PERSONA_NAME_ENFORCEMENT_PROMPT = "Your name is {name}. Always refer to yourself as {name} in your responses and in the first person."
    
class DevelopmentConfig(Config):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000

class ProductionConfig(Config):
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5000
    # In production, you would set more restrictive CORS settings
    CORS_ORIGINS = ['https://yourdomain.com']  # Replace with your actual domain

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
