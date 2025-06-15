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
                                    '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')
