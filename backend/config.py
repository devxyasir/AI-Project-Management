"""
Configuration settings for the Flask backend
"""
import os

class Config:
    """Configuration settings for the application"""
    
    # Flask settings
    DEBUG = os.environ.get('FLASK_DEBUG', True)
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # API keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 
                                    'API_KEY')
