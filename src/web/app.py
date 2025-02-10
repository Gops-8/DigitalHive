import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
import concurrent.futures
import requests
import json
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging  # Import logging module
import time


def timer(func):
    """Decorator to measure the runtime of functions."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # or time.time()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        # Log the elapsed time; you can also show it in the Streamlit interface.
        logging.info("Function %s took %.2f seconds", func.__name__, elapsed)
        st.write(f"Function **{func.__name__}** took **{elapsed:.2f}** seconds to complete.")
        return result
    return wrapper

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Change to logging.INFO or logging.ERROR to reduce verbosity
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure the src directory is in the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Import custom modules
from src.core.scraper import WebScraper
from src.core.content_analyzer import ContentAnalyzer
from src.core.data_processer import DataProcessor
from src.utils.components import Components
from src.utils.auth import AuthManager
from src.core.advanced_analytics import AdvancedAnalytics
from src.utils.cache import AnalysisCache

class WebApp:
    def __init__(self):
        self.init_session()
        self.components = Components()
        self.scraper = WebScraper()
        self.processor = DataProcessor()
        self.auth_manager = AuthManager()
        self.analytics = AdvancedAnalytics()
        self.cache = AnalysisCache()
        self.model = None

    def init_session(self):
        """Initialize session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'results' not in st.session_state:
            st.session_state.results = None
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = "llama3.1:8b"
        logging.debug("Session initialized: %s", st.session_state)

    def run(self):
        """Run the Streamlit app."""
        if not st.session_state.authenticated:
            st.set_page_config(page_title="Corporate Ranking AI", layout="centered", page_icon="assets/logo.jpg")
            self.components.show_login(auth_manager=self.auth_manager)
        else:
            st.set_page_config(page_title="Corporate Ranking AI", layout="wide", page_icon="assets/logo.jpg")
            self.show_main_page()

    def show_main_page(self):
        """Display the main page with tabs."""
        logging.debug("Displaying main page.")
        col1, col2 = st.columns([1, 8])
        with col1:
            st.image("assets/logo.jpg", width=100)
        with col2:
            st.title("Corporate Ranking AI")
        
        tabs = st.tabs(["AI-Powered Data Extractor", "Competitive Insights & SEO Analysis"])
        
        with tabs[0]:
            st.markdown("""
            **AI-Powered Data Extractor:**
            - Extracts essential business information such as:
              - Keywords
              - Target audience
              - Location
              - Products & Services
            - Expected Input: Excel file with a single column containg URLS.
            """)
            self.ai_based_extractor()
        
        with tabs[1]:
            st.markdown("""
            **Competitive Insights & SEO Analysis:**
            - Provides advanced insights such as:
              - Google My Business (GMB) verification
              - Non-indexed pages analysis
              - SEO visibility insights
            - Expected Input: CSV output from AI-Powered Data Extractor with business-related details
                         (must have Keywords_1, product_serivices_1, urls ).
            - Expected Output: CSV file with additional insights
            """)
            self.competitive_insights()
    
    def ai_based_extractor(self):
        """Handle the AI-Powered Data Extraction process."""
        logging.debug("Starting AI-based extractor.")
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = "llama3.2:3b"
        uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
        if uploaded_file:
            st.session_state.selected_model = st.selectbox("Select Model", ["llama3.1:8b", "llama3.2:3b", "llama3.2"])
            st.info(f"Uploaded: {uploaded_file.name}")
            logging.debug("File uploaded: %s", uploaded_file.name)
            if st.button("Start Data Extraction"):
                logging.debug("Start Data Extraction button pressed.")
                self.process_basic_analysis(uploaded_file)
    
    def competitive_insights(self):
        """Handle the Competitive Insights & SEO Analysis process."""
        logging.debug("Starting Competitive Insights analysis.")
        search_method = st.selectbox(
            "Select Search Method",
            ("Basic Google Search", "Serper.dev API")
        )

        api_key = None
        if search_method == "Serper.dev API":
            api_key = st.text_input("Enter your Serper.dev API Key", type="password")

        uploaded_file = st.file_uploader("Upload AI-Powered Data Extractor Output (CSV or Excel)", type=['csv', 'xlsx', 'xls'])
        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")
            gmb_check = st.checkbox("Check Google My Business (GMB)")
            non_index_pages_check = st.checkbox("Count Non-Indexed Pages")
            if st.button("Start Competitive Insights Analysis"):
                logging.debug("Start Competitive Insights Analysis button pressed.")
                self.process_advanced_analysis(uploaded_file, gmb_check, non_index_pages_check, search_method, api_key)
    @timer
    def process_basic_analysis(self, uploaded_file):
        """Handles basic web scraping and content analysis in batches with caching and indicators"""
        logging.debug("Processing basic analysis started.")
        st.write("Processing basic analysis...")
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = f"input/temp_{timestamp}.xlsx"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        logging.debug("File saved to %s", input_path)
        urls = self.processor.read_excel_to_url(input_path)
        logging.debug("URLs extracted: %s", urls)
        if not urls:
            st.error("No URLs found in the uploaded file.")
            logging.error("No URLs found in the uploaded file.")
            return
        results = []
        batch_size = 40
        total_batches = len(urls) // batch_size + (1 if len(urls) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        timer_text = st.empty() 
        status_text.text(f"Total URLs: {len(urls)} | Processing in {total_batches} batches")
        selected_model = st.session_state.selected_model
        logging.debug("Selected model for analysis: %s", selected_model)
        for i in range(0, len(urls), batch_size):
            batch_start = time.perf_counter() 
            batch_urls = urls[i:i + batch_size]
            logging.debug("Processing batch %d: %s", i // batch_size + 1, batch_urls)
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                # Pass the selected_model to process_url using a lambda or partial
                batch_results = list(executor.map(lambda url: self.process_url(url, selected_model), batch_urls))
            results.extend(batch_results)
            df = pd.DataFrame(results)
            if not df.empty:
                st.session_state.results = df
                self.components.display_results(df)
            progress_bar.progress(min((i + batch_size) / len(urls), 1.0))
            status_text.text(f"Currently Processing Batch {i // batch_size + 1} of {total_batches}")
            logging.debug("Completed batch %d", i // batch_size + 1)
            batch_end = time.perf_counter()  # End timer for this batch
            elapsed = batch_end - batch_start
            timer_text.text(f"Batch {i // batch_size + 1} processed in {elapsed:.2f} seconds")
        logging.debug("Basic analysis completed.")

    def process_url(self, url, model):
        logging.debug("Processing URL: %s with model: %s", url, model)
        try:
            clean_url = self.processor.clean_url(url)
            cached_data = self.cache.get(clean_url)
            if not cached_data:
                scraped_data = self.scraper.scrape_website(clean_url)
                self.cache.set(clean_url, scraped_data)
                logging.debug("Scraped data for URL %s", clean_url)
            else:
                scraped_data = cached_data
                logging.debug("Using cached data for URL %s", clean_url)
            analyzer = ContentAnalyzer(model=model)
            analysis = analyzer.analyze_with_ollama(scraped_data['content'], clean_url)
            logging.debug("Analysis result for URL %s: %s", clean_url, analysis)
            location = analysis.get('location', '')
            keywords = analysis.get('keywords', '')
            target_audiences = analysis.get('target_audience', '')
            business_name = analysis.get('business_name', '')
            product_services = analysis.get('products_services', '')
            
            if not keywords and not product_services:
                logging.warning("Missing keywords and products for URL %s", url)
                return {'url': url, 'status': 'error', 'error': 'Missing keywords and products'}
            
            result = {'url': url, 'status': 'success', 'business_name': business_name, 'location': location}
            keyword_list = keywords.split(',')
            for i in range(5):
                result[f'keyword_{i+1}'] = keyword_list[i] if i < len(keyword_list) else ''
            product_services_list = product_services.split(',')
            for i in range(3):
                result[f'product_services_{i+1}'] = product_services_list[i] if i < len(product_services_list) else ''
            target_audience_list = target_audiences.split(',')
            for i in range(3):
                result[f'target_audiance_{i+1}'] = target_audience_list[i] if i < len(target_audience_list) else ''
            
            logging.debug("Result for URL %s: %s", url, result)
            return result
        except Exception as e:
            logging.error("Error processing URL %s: %s", url, e)
            return {'url': url, 'status': 'error', 'error': str(e)}
    @timer
    def process_advanced_analysis(self, uploaded_file, gmb_check, non_index_pages_check, search_method, api_key):
        """Handles advanced analytics in batches using multithreading."""
        logging.debug("Processing advanced analysis started.")
        # Create necessary directories
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)

        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = f"input/temp_{timestamp}.{uploaded_file.name.split('.')[-1]}"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        logging.debug("Advanced analysis file saved to %s", input_path)

        # Identify file type and read accordingly
        try:
            if uploaded_file.name.endswith('.csv'):
                # df = pd.read_csv(input_path)
                try:
                    df = pd.read_csv(input_path)
                except UnicodeDecodeError as e:
                    logging.warning("UTF-8 decoding failed: %s. Trying ISO-8859-1 encoding.", e)
                    df = pd.read_csv(input_path, encoding='ISO-8859-1')
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(input_path)
            else:
                st.error("Unsupported file format. Please upload a CSV or Excel file.")
                logging.error("Unsupported file format: %s", uploaded_file.name)
                return

        except Exception as e:
            st.error(f"Error reading file: {e}")
            logging.error("Error reading file %s: %s", input_path, e)
            return

        if df.empty:
            st.error("Uploaded file is empty or invalid.")
            logging.error("DataFrame is empty for file: %s", input_path)
            return

        results = []
        batch_size = 50
        total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        status_text.text(f"Total Rows: {len(df)} | Processing in {total_batches} batches | batch size : {batch_size} urls")
        logging.debug("Advanced analysis: %d rows to process in %d batches", len(df), total_batches)

        # Process in batches with multithreading
        for i in range(0, len(df), batch_size):
            batch_start = time.perf_counter()
            batch_rows = df.iloc[i:i + batch_size].to_dict(orient="records")
            logging.debug("Processing advanced analysis batch %d", i // batch_size + 1)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                batch_results = list(executor.map(
                    lambda row: self.process_row(row, search_method, api_key, gmb_check, non_index_pages_check),
                    batch_rows
                ))
            results.extend(batch_results)
            df_results = pd.DataFrame(results)

            if not df_results.empty:
                st.session_state.results = df_results
                self.components.display_results(df_results)

            progress_bar.progress(min((i + batch_size) / len(df), 1.0))
            status_text.text(f"Processing Batch {i // batch_size + 1} of {total_batches}")
            logging.debug("Completed advanced analysis batch %d", i // batch_size + 1)

        logging.debug("Advanced analysis completed.")

    def process_row(self, row, search_method, api_key, gmb_check, non_index_pages_check):
        """Process a single row using multithreading and prioritize keyword search."""
        logging.debug("Processing row: %s", row)
        try:
            # Extract search query: prioritize keywords, then use product_services
            search_query = str(row.get('keyword_1', '')).strip()
            if not search_query:
                search_query = str(row.get('product_services_1', '')).strip()

            if not search_query:
                logging.warning("No valid search query in row: %s", row)
                return {**row, "status": "skipped", "error": "No valid search query"}

            # Perform the search
            try:
                if search_method == "Serper.dev API" and api_key:
                    search_result = self.analytics.search_serper(search_query, api_key)
                else:
                    search_result = self.analytics.fetch_google_results(search_query, row.get('location', ''))

                if not search_result or (isinstance(search_result, dict) and "error" in search_result):
                    logging.error("Search error for query '%s': %s", search_query, search_result)
                    return {**row, "status": "error", "error": search_result.get("error", "No search results")}

            except Exception as e:
                logging.error("Exception during search for query '%s': %s", search_query, e)
                return {**row, "status": "error", "error": str(e)}

            # Clean & filter URLs
            competitors = self.analytics.clean_and_filter_urls(search_result, row.get('url', ''))
            if not competitors:
                logging.error("No valid competitors found for query '%s'", search_query)
                return {**row, "status": "error", "error": "No valid competitors"}

            # Ensure we always return 3 competitor columns
            result = {
                **row,
                "search_query": search_query,
                "status": "success",
                "top_competitor_1": competitors[0] if len(competitors) > 0 else "",
                "top_competitor_2": competitors[1] if len(competitors) > 1 else "",
                "top_competitor_3": competitors[2] if len(competitors) > 2 else ""
            }
            logging.debug("Processed row result: %s", result)
            return result

        except Exception as e:
            logging.error("Error processing row %s: %s", row, e)
            return {**row, "status": "error", "error": str(e)}

if __name__ == "__main__":
    logging.debug("Starting WebApp.")
    app = WebApp()
    app.run()
