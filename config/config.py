import os
from dotenv import load_dotenv

load_dotenv()

# Scraping Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 2  # seconds between requests

# App configuration
APP_CONFIG = {
    'PAGE_TITLE': "Corporate Ranking AI",
    'PAGE_ICON': "🌐",
    'LAYOUT': "wide"
}

# File paths
PATHS = {
    'INPUT_DIR': 'input',
    'OUTPUT_DIR': 'output',
    'SCRAPING_DIR': 'output/scraping',
    'ANALYSIS_DIR': 'output/analysis'
}

# Create necessary directories
for path in PATHS.values():
    os.makedirs(path, exist_ok=True)
    
# SCRAPE_API_KEY  = '678f5447f29bc3xNwg9SwoCCZ381'
