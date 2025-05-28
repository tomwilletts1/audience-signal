import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    DEFAULT_TEXT_MODEL = "gpt-4"
    DEFAULT_VISION_MODEL = "gpt-4-vision-preview"
    DEFAULT_TEMPERATURE = 0.7
    
    # Persona Presets
    PERSONA_PRESETS = {
        "Young Graduate Woman": "A 24-year-old recent college graduate working in marketing. She's tech-savvy, values work-life balance, and is conscious about sustainability. She enjoys yoga, travel, and trying new restaurants.",
        "Mid-Career Professional": "A 35-year-old marketing manager with 10 years of experience. He's focused on career growth, enjoys golf, and values quality time with family. He's interested in personal development and networking.",
        "Retired Couple": "A couple in their early 60s who recently retired. They enjoy gardening, travel, and spending time with grandchildren. They value tradition and quality over quantity.",
        "Small Business Owner": "A 45-year-old entrepreneur running a local coffee shop. She's community-focused, values authenticity, and is always looking for ways to grow her business sustainably.",
        "Tech Enthusiast": "A 30-year-old software developer who loves staying on top of the latest technology trends. He's interested in gadgets, gaming, and digital privacy. He values innovation and efficiency.",
        "Post Graduate Student": "A 22 to 24 year Post Graduate Student at University, who is looking to begin his career in the marketing industry and has very driven attitude. He values spending time with friends and is interested in cost-effectiveness."
    }

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
