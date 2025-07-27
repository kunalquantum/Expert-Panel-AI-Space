# Configuration file for the Expert-Panel Chatbot

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyCb-1D2gC4eMR0VC9idxhH6AVMLZugfro8"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# API Generation Configuration
GENERATION_CONFIG = {
    "temperature": 0.7,
    "topK": 40,
    "topP": 0.95,
    "maxOutputTokens": 1024
}

# App Configuration
APP_CONFIG = {
    "page_title": "Expert-Panel Chatbot",
    "page_icon": "🤖",
    "layout": "wide"
}

# Default Expert Panel
DEFAULT_EXPERTS = ["Healthcare", "Education"]
DEFAULT_TONE = "Neutral"

# Conversation Settings
MAX_HISTORY_CONTEXT = 3  # Number of previous messages to include in context
REQUEST_TIMEOUT = 30  # API request timeout in seconds 