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
        self.analyzer = ContentAnalyzer()
        self.auth_manager = AuthManager()
        self.analytics = AdvancedAnalytics()
        self.cache = AnalysisCache()

    def init_session(self):
        """Initialize session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'results' not in st.session_state:
            st.session_state.results = None

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
        col1, col2 = st.columns([1, 8])
        with col1:
            st.image("assets/logo.jpg", width=100)
        with col2:
            st.title("Corporate Ranking AI")
        
        tabs = st.tabs(["AI-Powered Data Extractor", "Competitive Insights & SEO Analysis"])
        
        with tabs[0]:
            st.markdown("**This tool extracts essential business information such as keywords, target audience, location, products, and services from the given URLs.**")
            self.ai_based_extractor()
        with tabs[1]:
            st.markdown("**This tool provides advanced competitive insights, including Google My Business (GMB) verification, non-indexed pages analysis, and SEO visibility analysis.**")
            self.competitive_insights()
    
    def ai_based_extractor(self):
        """Handle the AI-Powered Data Extraction process."""
        uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")
            if st.button("Start Data Extraction"):
                self.process_basic_analysis(uploaded_file)
    
    def competitive_insights(self):
        """Handle the Competitive Insights & SEO Analysis process."""
        search_method = st.selectbox(
            "Select Search Method",
            ("Basic Google Search", "Serper.dev API")
        )

        api_key = None
        if search_method == "Serper.dev API":
            api_key = st.text_input("Enter your Serper.dev API Key", type="password")

        uploaded_file = st.file_uploader("Upload AI-Powered Data Extractor Output (CSV)", type=['csv'])
        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")
            gmb_check = st.checkbox("Check Google My Business (GMB)")
            non_index_pages_check = st.checkbox("Count Non-Indexed Pages")
            if st.button("Start Competitive Insights Analysis"):
                self.process_advanced_analysis(uploaded_file, gmb_check, non_index_pages_check, search_method, api_key)
    
    def process_basic_analysis(self, uploaded_file):
        """Handles basic web scraping and content analysis in batches with caching and indicators"""
        st.write("Processing basic analysis...")
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = f"input/temp_{timestamp}.xlsx"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        urls = self.processor.read_excel_to_url(input_path)
        if not urls:
            st.error("No URLs found in the uploaded file.")
            return
        results = []
        batch_size = 100
        total_batches = len(urls) // batch_size + (1 if len(urls) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        status_text.text(f"Total URLs: {len(urls)} | Processing in {total_batches} batches")
        
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                batch_results = list(executor.map(self.process_url, batch_urls))
            results.extend(batch_results)
            df = pd.DataFrame(results)
            if not df.empty:
                st.session_state.results = df
                self.components.display_results(df)
            progress_bar.progress(min((i + batch_size) / len(urls), 1.0))
            status_text.text(f"Currently Processing Batch {i // batch_size + 1} of {total_batches}")
    
    def process_url(self, url):
        try:

            clean_url = self.processor.clean_url(url)
            cached_data = self.cache.get(clean_url)
            if not cached_data:
                scraped_data = self.scraper.scrape_website(clean_url)
                self.cache.set(clean_url, scraped_data)
            else:
                scraped_data = cached_data
            
            analysis = self.analyzer.analyze_with_ollama(scraped_data['content'], clean_url)
            location = analysis.get('location', '')
            keywords = analysis.get('keywords', '')
            target_audiences = analysis.get('target_audience', '')
            business_name = analysis.get('business_name', '')
            product_services = analysis.get('products_services', '')
            
            if not keywords and not product_services:
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
            
            return result
        except Exception as e:
            return {'url': url, 'status': 'error', 'error': str(e)}


    def process_advanced_analysis(self, uploaded_file, gmb_check, non_index_pages_check, search_method, api_key):
        """Handles advanced analytics in batches using multithreading."""
        
        # Create necessary directories
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)

        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = f"input/temp_{timestamp}.{uploaded_file.name.split('.')[-1]}"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Identify file type and read accordingly
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(input_path)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(input_path)
            else:
                st.error("Unsupported file format. Please upload a CSV or Excel file.")
                return

        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        if df.empty:
            st.error("Uploaded file is empty or invalid.")
            return

        results = []
        batch_size = 100
        total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        status_text.text(f"Total Rows: {len(df)} | Processing in {total_batches} batches")

        # Process in batches with multithreading
        for i in range(0, len(df), batch_size):
            batch_rows = df.iloc[i:i + batch_size].to_dict(orient="records")

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
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


    def process_row(self, row, search_method, api_key, gmb_check, non_index_pages_check):
        """Process a single row using multithreading and prioritize keyword search."""
        try:
            # Extract search query: prioritize keywords, then use product_services
            search_query = str(row.get('keyword_1', '')).strip()
            if not search_query:
                search_query = str(row.get('product_services_1', '')).strip()

            if not search_query:
                return {**row, "status": "skipped", "error": "No valid search query"}

            # Perform the search
            try:
                if search_method == "Serper.dev API" and api_key:
                    search_result = self.analytics.search_serper(search_query, api_key)
                else:
                    search_result = self.analytics.fetch_google_results(search_query, row.get('location', ''))

                if not search_result or isinstance(search_result, dict) and "error" in search_result:
                    return {**row, "status": "error", "error": search_result.get("error", "No search results")}

            except Exception as e:
                return {**row, "status": "error", "error": str(e)}

            # Clean & filter URLs
            competitors = self.analytics.clean_and_filter_urls(search_result, row.get('url', ''))
            if not competitors:
                return {**row, "status": "error", "error": "No valid competitors"}

            # Ensure we always return 3 competitor columns
            return {
                **row,
                "search_query": search_query,
                "status": "success",
                "top_competitor_1": competitors[0] if len(competitors) > 0 else "",
                "top_competitor_2": competitors[1] if len(competitors) > 1 else "",
                "top_competitor_3": competitors[2] if len(competitors) > 2 else ""
            }

        except Exception as e:
            return {**row, "status": "error", "error": str(e)}


if __name__ == "__main__":
    app = WebApp()
    app.run()
