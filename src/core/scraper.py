import requests
from bs4 import BeautifulSoup
import re
from config.config import HEADERS, REQUEST_TIMEOUT
from urllib.parse import urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebScraper:
    def __init__(self):
        self.headers = HEADERS

    def scrape_website(self, url):
        """Scrape website content"""
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=REQUEST_TIMEOUT,
                verify=False
            )
            # Check for HTTP errors
            if response.status_code != 200:
                raise Exception(f"HTTP error {response.status_code} for {url}")
            
            # # Check if response contains known Cloudflare error patterns
            # if "Error code 520" in response.text or "Cloudflare" in response.text:
            #     raise Exception(f"Cloudflare error encountered for {url}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = ' '.join([
                p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])
            ])
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # If no content is found, raise an exception.
            if not text_content:
                raise Exception(f"No readable content found for {url}")
            
            # Extract metadata
            metadata = {
                'title': soup.title.text if soup.title else '',
                'meta_description': (
                    soup.find('meta', {'name': 'description'})['content']
                    if soup.find('meta', {'name': 'description'}) else ''
                )
            }
            
            return {
                'content': text_content,
                'metadata': metadata
            }
            
        except Exception as e:
            raise Exception(f"Error scraping {url}: {str(e)}")
        
