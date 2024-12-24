import os
from dotenv import load_dotenv

load_dotenv()

# Scraping Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 2  # seconds between requests
