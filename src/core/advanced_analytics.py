import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import time
import re
class AdvancedAnalytics:
    def __init__(self, headers=None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        

    def fetch_google_results(self, product, location, pages=1):
        """Fetch Google search results for a given product and location with rate limiting."""
        base_url = "https://www.google.com/search"
        query = f"{product} in {location}"
        all_links = []

        for page in range(pages):
            start = page * 10
            params = {'q': '+'.join(query.split()), 'start': start}
            response = requests.get(base_url, params=params, headers=self.headers)
            time.sleep(2)  # Introduce a delay of 2 seconds between requests
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for result in soup.select('a'):
                href = result.get('href')
                if href and 'http' in href:
                    all_links.append(href)

        return all_links

    def clean_and_filter_urls(self, urls, origin_url):
        """Clean and filter URLs to extract unique competitors."""
        unique_urls = set()
        base_urls = []
        excluded_domains = {"google", "facebook", "yelp", "instagram","wikipedia", "amazon","walmart","reddit","linkedin","etsy","youtube"}

        for url in urls:
            parsed = urlparse(url)

            # Skip URLs with excluded domains
            if any(domain in parsed.netloc for domain in excluded_domains):
                continue
            
            # Extract base URL
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Add to unique URLs if not already present and not equal to the origin URL
            if base_url not in unique_urls and base_url != origin_url:
                unique_urls.add(base_url)
                base_urls.append(base_url)

            # Stop when we have 5 unique URLs
            if len(base_urls) == 5:
                break

        return base_urls

    def check_gmb_setup(self, url):
        """Check if a website has GMB setup."""
        try:
            response = requests.get(url, headers=self.headers, timeout=20,verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for LocalBusiness schema
            schema = soup.find_all('script', type='application/ld+json')
            for script in schema:
                if script.string:
                  try:
                      data = json.loads(script.string)
                      if '@type' in data and data['@type'] == 'LocalBusiness':
                          return 'Yes'
                  except json.JSONDecodeError:
                      continue

            # Additional checks for GMB markers
            if "google.com/maps" in response.text or "reviews" in response.text:
                return 'Yes'

        except requests.exceptions.RequestException as e:
            print(f"Error checking GMB setup for {url}: {e}")
            return 'N/A'

        return 'No'

    def count_non_indexed_pages(self, url):
        """Count the number of non-indexed pages for a given domain."""
        try:
            site_query = f"site:{urlparse(url).netloc}"  # Google site query
            search_url = f"https://www.google.com/search?q={site_query}"
            response = requests.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check if there are zero results
            no_results_text = soup.find("div", class_="card-section")
            if no_results_text and "did not match any documents" in no_results_text.text:
                return 0

            # Count results (example logic, may need refinement)
            result_stats = soup.find("div", id="result-stats")
            if result_stats:
                match = re.search(r"About ([\d,]+) results", result_stats.text)
                if match:
                    return int(match.group(1).replace(",", ""))

        except Exception as e:
            print(f"Error counting non-indexed pages for {url}: {e}")
        
        return 0

    def count_total_pages(self, url):
        """Estimate the total number of pages for a given domain."""
        try:
            response = requests.get(f"{url}/sitemap.xml", headers=self.headers, timeout=10)
            if response.status_code == 200:
                # Parse the response as XML using lxml
                soup = BeautifulSoup(response.text, "lxml-xml")
                total_pages = len(soup.find_all("url"))
                return total_pages
            else:
                return 100  # Default assumption for total pages
        except Exception as e:
            print(f"Error counting total pages for {url}: {e}")
            return 100  # Default assumption for total pages

        
    def find_top_competitors_with_gmb_and_indexed_pages(self, product, location, pages=1):
        """Find top competitors, check GMB setup, and count indexed pages."""
        competitors = self.find_top_competitors(product, location, pages)
        competitors_info = {
            url: {
                "gmb_setup": self.check_gmb_setup(url),
                "indexed_pages": self.count_non_indexed_pages(url)
            } for url in competitors
        }
        return competitors_info

    def find_top_competitors(self, product, location,origin_url, pages=1 ):
        """Find top competitors for a given product and location."""
        raw_links = self.fetch_google_results(product, location, pages=pages)
        top_competitors = self.clean_and_filter_urls(raw_links, origin_url)
        return top_competitors


