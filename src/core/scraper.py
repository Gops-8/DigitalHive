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
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = ' '.join([
                p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])
            ])
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            if not text_content:
                raise Exception(f"Unable to access the website or content is blank for {url}")

            # Extract metadata
            metadata = {
                'title': soup.title.text if soup.title else '',
                'meta_description': soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else ''
            }
            
            return {
                'content': text_content,
                'metadata': metadata
            }
            
        except Exception as e:
            raise Exception(f"Error scraping {url}: {str(e)}")
        
# class EnhancedWebScraper:
#     def __init__(self, headers):
#         self.headers = headers

#     def scrape_website(self, url, features):
#         """
#         Scrape website content and include additional information based on selected features.

#         :param url: The URL to scrape.
#         :param features: A dictionary of feature flags indicating which additional data to collect.
#         :return: A dictionary containing the scraped data and additional information.
#         """
#         try:
#             response = requests.get(url, headers=self.headers, timeout=10, verify=False)
#             soup = BeautifulSoup(response.text, 'html.parser')

#             # Extract text content
#             text_content = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])])
#             text_content = re.sub(r'\s+', ' ', text_content).strip()

#             # Extract metadata
#             metadata = {
#                 'title': soup.title.text if soup.title else '',
#                 'meta_description': soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else ''
#             }

#             # Initialize result
#             result = {
#                 'content': text_content,
#                 'metadata': metadata
#             }

#             # Include GMB setup check if selected
#             if features.get("gmb"):
#                 result['gmb_setup'] = self.check_gmb_setup(soup, url)

#             # Include indexed and non-indexed page counts if selected
#             if features.get("non_index_pages"):
#                 indexed_pages, total_pages = self.count_pages(url)
#                 result['indexed_pages'] = indexed_pages
#                 result['non_indexed_pages'] = max(0, total_pages - indexed_pages)

#             return result

#         except Exception as e:
#             raise Exception(f"Error scraping {url}: {str(e)}")

#     def check_gmb_setup(self, soup, url):
#         """Check for GMB setup in schema or known patterns."""
#         try:
#             # Look for LocalBusiness schema
#             schema = soup.find_all('script', type='application/ld+json')
#             for script in schema:
#                 if script.string:
#                     data = json.loads(script.string)
#                     if '@type' in data and data['@type'] == 'LocalBusiness':
#                         return 'Yes'
#             # Fallback: Look for other indicators
#             response = requests.get(url, headers=self.headers, timeout=10, verify=False)
#             if "google.com/maps" in response.text or "reviews" in response.text:
#                 return 'Yes'
#         except Exception:
#             pass
#         return 'No'

#     def count_pages(self, url):
#         """Estimate indexed and total pages."""
#         try:
#             # Query Google for indexed pages
#             site_query = f"site:{urlparse(url).netloc}"
#             search_url = f"https://www.google.com/search?q={site_query}"
#             response = requests.get(search_url, headers=self.headers, timeout=10)
#             soup = BeautifulSoup(response.text, 'html.parser')

#             # Count indexed results
#             result_stats = soup.find("div", id="result-stats")
#             indexed_pages = 0
#             if result_stats:
#                 match = re.search(r"About ([\d,]+) results", result_stats.text)
#                 if match:
#                     indexed_pages = int(match.group(1).replace(",", ""))

#             # Estimate total pages from sitemap
#             total_pages = self.count_total_pages(url)

#             return indexed_pages, total_pages
#         except Exception:
#             return 0, 100  # Default assumption

#     def count_total_pages(self, url):
#         """Estimate total pages via sitemap.xml."""
#         try:
#             response = requests.get(f"{url}/sitemap.xml", headers=self.headers, timeout=10)
#             if response.status_code == 200:
#                 soup = BeautifulSoup(response.text, 'lxml-xml')
#                 return len(soup.find_all("url"))
#         except Exception:
#             pass
#         return 100  # Default fallback
