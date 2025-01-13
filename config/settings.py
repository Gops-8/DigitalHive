import os
from dotenv import load_dotenv

load_dotenv()

APP_CONFIG = {
    'PAGE_TITLE': "Digital Hive",
    'PAGE_ICON': "🌐",
    'LAYOUT': "native"
}
## models  tested 
# llama 2 7b 
# llama3.1:8b
# hermes3 8b
# llama3.2 3b
# phi4

OLLAMA_CONFIG = {
    'BASE_URL': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
    'MODEL': os.getenv('OLLAMA_MODEL', 'llama3.1:8b'),
    'TEMPERATURE': 0.21
}

# Remote configuration URL (e.g., GitHub Gist or secure API endpoint)
AUTH_CONFIG_URL = "https://raw.githubusercontent.com/Gops-8/auth-config/main/config.json"

PATHS = {
    'INPUT': 'input',
    'OUTPUT': 'output/analysis',
    'CACHE': 'output/cache'
}
