import requests
import json
import hashlib
import random
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pandas as pd
from src.utils.cache import AnalysisCache
from src.utils.rate_limiter import RateLimiter
import logging

# Configure logging for this module
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AdvancedAnalytics:
    def __init__(self):
        # Use the competitor cache folder for caching in competitive analysis.
        self.cache = AnalysisCache(cache_dir="output/cache_competitor")
        logging.debug("Initialized AdvancedAnalytics with cache.")

    def hash_query(self, query):
        hash_value = hashlib.md5(query.encode('utf-8')).hexdigest()
        logging.debug("Hashed query '%s' to '%s'", query, hash_value)
        return hash_value

    def fetch_google_results(self, product, location, pages=1):
        logging.debug("Fetching Google results for product: '%s' in location: '%s'", product, location)
        base_url = "https://www.google.com/search"
        query = f"{product} in {location}"
        all_links = []
        rate_limiter = RateLimiter(requests_per_minute=15)

        for page in range(pages):
            rate_limiter.wait()
            start = page * 10
            params = {'q': '+'.join(query.split()), 'start': start}
            USER_AGENTS = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
            ]
            headers = {"User-Agent": random.choice(USER_AGENTS)}

            for attempt in range(3):
                try:
                    logging.debug("Attempt %d: Sending request to Google for query: '%s'", attempt+1, query)
                    response = requests.get(base_url, params=params, headers=headers)
                    logging.debug("Response status code: %s", response.status_code)
                    response.raise_for_status()
                    if response.status_code == 429:
                        logging.warning("Google is rate-limiting us. Retrying after 60 seconds...")
                        time.sleep(60)
                        continue
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for result in soup.select('a'):
                        href = result.get('href')
                        if href and 'http' in href:
                            all_links.append(href)
                    logging.debug("Fetched %d links from Google", len(all_links))
                    return all_links
                except requests.exceptions.RequestException as e:
                    logging.error("Error fetching Google results on attempt %d: %s", attempt+1, str(e))
                    time.sleep(5)  

        logging.debug("Returning %d links after retries", len(all_links))
        return all_links

    def clean_and_filter_urls(self, urls, origin_url):
        logging.debug("Cleaning and filtering URLs, origin_url: %s", origin_url)
        unique_urls = set()
        filtered_competitors = []
        # ... (exclusions and known domains code as needed)

        origin_url_normalized = origin_url if origin_url.startswith("http") else "http://" + origin_url

        for item in urls:
            if isinstance(item, dict):
                url_str = item.get("link", "")
                position = item.get("position")
            else:
                url_str = item
                position = None

            parsed = urlparse(url_str)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            domain = parsed.netloc.lower()
            if not domain:
                continue
            # Exclusion logic can be added here if needed.
            if base_url not in unique_urls and base_url != origin_url_normalized:
                unique_urls.add(base_url)
                filtered_competitors.append({"link": base_url, "position": position})
            if len(filtered_competitors) == 3:
                break

        logging.debug("Filtered competitors: %s", filtered_competitors)
        return filtered_competitors

    def check_gmb_listing(self, business_name, location):
        logging.debug("Checking GMB listing for business: '%s', location: '%s'", business_name, location)
        search_query = f"{business_name} {location} Google My Business"
        search_results = self.fetch_google_results(search_query, location)
        for item in search_results:
            url = item if isinstance(item, str) else item.get("link", "")
            if "google.com/maps/place/" in url:
                logging.debug("Found GMB listing for business: '%s': %s", business_name, url)
                return {"exists": True, "url": url}
        logging.debug("No GMB listing found for business: '%s'", business_name)
        return {"exists": False, "url": None}

    def analyze_non_indexed_pages(self, domain):
        logging.debug("Analyzing non-indexed pages for domain: '%s'", domain)
        sitemap_url = domain.rstrip('/') + '/sitemap.xml'
        try:
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code != 200:
                logging.warning("Sitemap not found at %s (status code %d)", sitemap_url, response.status_code)
                return 0
            soup = BeautifulSoup(response.content, 'xml')
            loc_tags = soup.find_all('loc')
            urls = [tag.text for tag in loc_tags]
            count_noindex = 0
            for url in urls[:20]:
                try:
                    page_response = requests.get(url, timeout=5)
                    if page_response.status_code == 200:
                        page_soup = BeautifulSoup(page_response.text, 'html.parser')
                        meta_robots = page_soup.find('meta', attrs={'name': 'robots'})
                        if meta_robots and 'noindex' in meta_robots.get('content', '').lower():
                            count_noindex += 1
                except Exception as e:
                    logging.error("Error fetching URL %s: %s", url, e)
            logging.debug("Found %d non-index pages out of %d sitemap URLs", count_noindex, len(urls))
            return count_noindex
        except Exception as e:
            logging.error("Error fetching sitemap from %s: %s", sitemap_url, e)
            return 0

    def search_serper(self, query, api_key):
        logging.debug("Performing Serper.dev API search for query: '%s'", query)
        cache_key = self.hash_query(query)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logging.debug("Cache hit for Serper.dev query: '%s'", query)
            return cached_result
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "q": query,
            "hl": "en",
            "gl": "us",
            "num": 10
        })
        url = "https://google.serper.dev/search"
        try:
            response = requests.post(url, headers=headers, data=payload)
            logging.debug("Serper.dev API response status code: %s", response.status_code)
            response.raise_for_status()
            result = response.json()
            results_list = [
                {"link": item.get("link"), "position": item.get("position")}
                for item in result.get("organic", [])
                if item.get("link")
            ]
            if not results_list:
                logging.warning("No results found for query: '%s'", query)
                return {"error": f"No results found for query: {query}"}
            self.cache.set(cache_key, results_list)
            logging.info("Retrieved %d results for query: '%s'", len(results_list), query)
            return results_list
        except requests.exceptions.RequestException as e:
            error_message = f"API request failed: {str(e)}"
            logging.error("Serper.dev API request failed for query '%s': %s", query, error_message)
            return {"error": error_message}
        except json.JSONDecodeError:
            error_message = f"Failed to parse JSON response from Serper.dev for query: {query}"
            logging.error("JSON decode error for query '%s': %s", query, error_message)
            return {"error": error_message}
