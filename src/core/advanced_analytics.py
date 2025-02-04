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


class AdvancedAnalytics:
    def __init__(self):
        self.cache = AnalysisCache()

    def hash_query(self, query):
        """Generate a unique hash for a given query to use as a cache key."""
        return hashlib.md5(query.encode('utf-8')).hexdigest()

    def fetch_google_results(self, product, location, pages=1):
        """Fetch Google search results for a given product and location with rate limiting and retries."""
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

            for _ in range(3):  # Retry up to 3 times
                try:
                    response = requests.get(base_url, params=params, headers=headers)
                    response.raise_for_status()
                    
                    if response.status_code == 429:
                        print("⚠️ Google is rate-limiting us. Retrying after 60 seconds...")
                        time.sleep(60)
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    for result in soup.select('a'):
                        href = result.get('href')
                        if href and 'http' in href:
                            all_links.append(href)

                    return all_links

                except requests.exceptions.RequestException as e:
                    print(f"❌ Error fetching Google results: {e}")
                    time.sleep(5)  # Wait before retrying

        return all_links  # Return whatever links were found


    def clean_and_filter_urls(self, urls, origin_url):
        """Clean and filter URLs to extract unique competitors."""
        unique_urls = set()
        base_urls = []
        known_domains = {
            "twitter", "paypal", "cloudflare", "google", "facebook", "pinterest",
            "apple", "youtube", "shopify", "amazon", "tiktok", "squarespace",
            "gmail", "blogspot.com", "adobe", "tumblr", "medium", "soundcloud",
            "gravatar", "nytimes", "jquery", "microsoft", "stripe", "reuters",
            "ebay", "wordpress", "etsy", "yelp", "tripadvisor", "glassdoor", 
            "trustpilot", "yellowpages", "linkedin", "bbb.org", "quora", "wikipedia",
            "angieslist", "homestars", "houzz", "sitejabber", 'linkedin', 'instagram', 'mastercard'
        }

        tld_exclusions = {".gov", ".org", ".edu", ".chat", ".blog", ".kpmg"}
        exclusions = {}
        try:
          with open('assets/domain_list.txt', 'r') as file:
              for line in file:
                  domain = line.strip().lower()
                  if domain:
                      key = domain[0]
                      exclusions.setdefault(key, set()).add(domain)
        except FileNotFoundError:
            print("⚠️ Domain list file not found. Skipping exclusions.")

        for url in urls:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            domain = parsed.netloc.lower()
            if not domain:
                continue
            if any(domain.endswith(tld) for tld in tld_exclusions):
                continue
            if any(known in domain for known in known_domains):
                continue
            first_letter = domain[0]
            if first_letter in exclusions and domain in exclusions[first_letter]:
                continue

            if base_url not in unique_urls and base_url != origin_url:
                unique_urls.add(base_url)
                base_urls.append(base_url)

            # Stop when we have 3 unique URLs
            if len(base_urls) == 3:
                break

        return base_urls

    def check_gmb_listing(self, business_name, location):
        """Check if a business has a Google My Business listing."""
        search_query = f"{business_name} {location}"
        search_results = self.fetch_google_results(search_query, location)
        for url in search_results:
            if "google.com/maps/place/" in url:
                return True
        return False

    def analyze_non_indexed_pages(self, domain):
        """Estimate the number of non-indexed pages for a given domain."""
        # Placeholder for non-indexed pages analysis logic
        # This would involve comparing the total number of pages on the website
        # to the number indexed by Google, possibly using tools like Screaming Frog
        return 0

    def analyze_competitors(self, data, search_method="Basic Google Search", api_key=None, gmb_check=False, non_index_pages_check=False):
        """
        Analyze competitors based on products and keywords.

        Parameters:
        - data: DataFrame containing 'product_services' and 'keywords' columns.
        - search_method: 'Basic Google Search' or 'Serper.dev API'.
        - api_key: API key for Serper.dev if selected.
        - gmb_check: Boolean to indicate if GMB listing check is required.
        - non_index_pages_check: Boolean to indicate if non-indexed pages analysis is required.

        Returns:
        - DataFrame with competitor analysis results.
        """
        for index, row in data.iterrows():
            # Ensure strings, avoid NaN issues
            product_services = str(row.get('product_services', '')).strip()
            keywords = str(row.get('keywords', '')).strip()

            products = product_services.split(',') if product_services else []
            keywords = keywords.split(',') if keywords else []
            search_terms = [term.strip() for term in products + keywords if term.strip()]

            if not search_terms:
                print(f"⚠️ Skipping row {index} due to missing search terms.")
                continue

            for term in search_terms:
                cache_key = self.hash_query(term)
                cached_result = self.cache.get(cache_key)

                if cached_result:
                    search_result = cached_result
                else:
                    if search_method == "Serper.dev API" and api_key:
                        search_result = self.search_serper(term, api_key)
                    else:
                        search_result = self.fetch_google_results(term, row.get('location', ''))

                    self.cache.set(cache_key, search_result)

                competitors = self.clean_and_filter_urls(search_result, row.get('url', ''))

                result = {
                    'search_term': term,
                    'competitors': competitors
                }

                if gmb_check:
                    result['gmb_listing'] = self.check_gmb_listing(row.get('business_name', ''), row.get('location', ''))

                if non_index_pages_check:
                    result['non_indexed_pages'] = self.analyze_non_indexed_pages(row.get('url', ''))

                results.append(result)

        return pd.DataFrame(results)

    def search_serper(self, query, api_key):
        """Perform a search using the Serper.dev API with caching and better error handling."""
        print(f"🔍 Performing Serper.dev API search for: {query}")

        # Check cache first
        cache_key = self.hash_query(query)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            print(f"🟢 Cache hit for query: {query}")
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
            response.raise_for_status()

            result = response.json()
            
            links = [item.get("link") for item in result.get("organic", []) if item.get("link")]

            if not links:
                print(f"⚠️ No results found for query: {query}")
                return {"error": f"No results found for query: {query}"}

            # Store result in cache
            self.cache.set(cache_key, links)
            print(f"✅ Retrieved {len(links)} results for query: {query}")
            return links

        except requests.exceptions.RequestException as e:
            error_message = f"❌ API request failed: {str(e)}"
            print(error_message)
            return {"error": error_message}

        except json.JSONDecodeError:
            error_message = f"❌ Failed to parse JSON response from Serper.dev for query: {query}"
            print(error_message)
            return {"error": error_message}
