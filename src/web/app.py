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
import io
from urllib.parse import urlparse
import logging

def timer(func):
    """Decorator to measure the runtime of functions."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        logging.info("Function %s took %.2f seconds", func.__name__, elapsed)
        st.write(f"Function **{func.__name__}** took **{elapsed:.2f}** seconds to complete.")
        return result
    return wrapper

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.core.scraper import WebScraper
from src.core.content_analyzer import ContentAnalyzer
from src.core.data_processer import DataProcessor
from src.utils.components import Components
from src.utils.auth import AuthManager
from src.core.advanced_analytics import AdvancedAnalytics
from src.utils.cache import AnalysisCache

# --------------------- WebApp Class (UI) ---------------------
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
        st.set_page_config(
            page_title="Corporate Ranking AI", 
            layout="wide", 
            page_icon="assets/logo.jpg"
        )
        st.markdown(
            """
            <style>
            /* Background image for the main app container */
            [data-testid="stAppViewContainer"] {
                background-image: url("assets/background.svg") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }
            
            /* Green button styling for all Streamlit buttons */
            [data-testid="stButton"] > div > button {
                background-color: #4CAF50 !important;
                color: white !important;
                border: none !important;
                padding: 8px 16px !important;
                font-size: 14px !important;
                cursor: pointer !important;
            }
            
            /* Optional hover effect */
            [data-testid="stButton"] > div > button:hover {
                background-color: #45a049 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


          
        if not st.session_state.authenticated:
            self.components.show_login(auth_manager=self.auth_manager)
        else:
            self.show_main_page()
            # The download button logic has been removed.

    def show_main_page(self):
        col1, col2 = st.columns([2, 7])
        with col1:
            st.image("assets/logo.jpg", width=100)
        with col2:
            st.title("Corporate Ranking AI")
        tabs = st.tabs(["AI-POWERED DATA EXTRACTOR", "COMPETITIVE INSIGHTS"])
        with tabs[0]:
            self.ai_based_extractor()
        with tabs[1]:
            self.competitive_insights()

    def ai_based_extractor(self):
        st.markdown(
        """
          **DATA EXTRACTION FACTORS**

          · **Business Name**  
          · **Business Location**  
          · **Keywords (5)**  
          · **Product/Service (3)**  
          · **Target Audience (3)**  

          · **Input Format:** (CSV/XLS/XLSX) with the website’s name as input (the column header must be **Domain**).  
          · **Output Format:** Displayed on screen
        """
        )
        # Use two columns: left (40%) and right (60%)
        col1, col2 = st.columns([4, 2])  # Adjust the ratio as needed

        with col1:
            st.subheader("1. Upload File")
            uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])

            st.subheader("2. Select Model")
            st.session_state.selected_model = st.selectbox(
                "Select Model", 
                ["llama3.1:8b", "llama3.2:latest", "deepseek-r1:32b", "llama3.3:70b", "olmo2:13b"]
            )

        with col2:
            st.subheader("3. Advanced Options")
            max_workers_options = [8, 16, 24]
            selected_max_workers = st.selectbox("Select Max Workers", options=max_workers_options)

            base_batch_sizes = [16, 32, 48, 64, 86]
            # Filter batch sizes to those that are multiples of the selected max workers
            filtered_batch_sizes = [bs for bs in base_batch_sizes if bs % selected_max_workers == 0]
            if not filtered_batch_sizes:
                filtered_batch_sizes = base_batch_sizes
            selected_batch_size = st.selectbox("Select Batch Size", options=filtered_batch_sizes)

        # Place the action button below both columns
        st.markdown('<div class="small-button">', unsafe_allow_html=True)
        if uploaded_file and st.button("Start Data Extraction", key="start_data_ext"):
            self.process_basic_analysis(uploaded_file, selected_batch_size, selected_max_workers)
        st.markdown('</div>', unsafe_allow_html=True)



    def competitive_insights(self):
        st.markdown(
        """
          **COMPETITIVE ANALYSIS FACTORS**

          · Top Competitor 1 (Website Only)  
          · Top Competitor 2 (Website Only)  
          · Top Competitor 1 SERP Rank  
          · Top Competitor 2 SERP Rank  

          · **Input Format:** (CSV/XLS/XLSX) with the columns **Domain**, **Keyword 1**, **Product/Service 1**.  
          · **Output Format:** Displayed on screen
        """
        )


        # --- Row 1: Search Method, API Key, and Submit Button ---
        row1 = st.columns([1.3, 2, 1])
        with row1[0]:
            search_method = st.selectbox("Select Search Method", ("Serper.dev API", "Basic Google Search"))
        with row1[1]:
            api_key_input = None
            if search_method == "Serper.dev API":
                if "serper_api" not in st.session_state:
                    api_key_input = st.text_input("Enter your Serper.dev API Key", type="password")
                else:
                    api_key_input = st.text_input("Update your Serper.dev API Key", type="password")
            else:
                st.info("Basic Google Search selected. No API key required.")
        with row1[2]:
            st.markdown('<div class="small-button">', unsafe_allow_html=True)
            if st.button("Submit API Key", key="submit_api_key"):
                st.session_state.serper_api = api_key_input
                st.success("API Key stored for this session.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Row 2: Left (File & Basic Options), Right (Advanced Options) ---
        row2 = st.columns([2, 2])  # Adjust ratios as needed (e.g., [1.5, 2], etc.)
        with row2[0]:
            uploaded_file = st.file_uploader("Upload Competitive Analysis Input File", type=['csv', 'xlsx', 'xls'])
            gmb_check = st.checkbox("Check Google My Business (GMB)")
            no_of_pages = st.radio("Number of SERP Pages", options=[1, 2])

        with row2[1]:
            max_workers_options = [8, 16, 24]
            comp_selected_max_workers = st.selectbox("Select Max Workers", options=max_workers_options, key="comp_workers")
            
            base_batch_sizes = [16, 32, 48, 64, 86]
            filtered_comp_batch_sizes = [bs for bs in base_batch_sizes if bs % comp_selected_max_workers == 0]
            if not filtered_comp_batch_sizes:
                filtered_comp_batch_sizes = base_batch_sizes
            comp_selected_batch_size = st.selectbox("Select Batch Size", options=filtered_comp_batch_sizes, key="comp_batch")

        # --- Action Button ---
        st.markdown('<div class="small-button">', unsafe_allow_html=True)
        if uploaded_file and st.button("Start Analysis", key="start_comp_analysis"):
            self.process_competitive_analysis(
                uploaded_file,
                gmb_check,
                no_of_pages,
                search_method,
                st.session_state.get("serper_api", None),
                comp_selected_batch_size,
                comp_selected_max_workers
            )
        st.markdown('</div>', unsafe_allow_html=True)



    @timer
    def process_basic_analysis(self, uploaded_file, batch_size, max_workers):
        st.write("Processing basic analysis...")
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = f"input/temp_{timestamp}.xlsx"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        try:
            df_input = pd.read_excel(input_path)
        except Exception as e:
            st.error("Error reading the Excel file.")
            return
        if "Domain" not in df_input.columns:
            st.error("Input file must have a column named 'Domain'.")
            return
        rows = df_input.to_dict(orient="records")
        results = []
        total_batches = len(rows) // batch_size + (1 if len(rows) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        timer_text = st.empty()
        status_text.text(f"Total Rows: {len(rows)} | Processing in {total_batches} batches")
        selected_model = st.session_state.selected_model
        for i in range(0, len(rows), batch_size):
            batch_start = time.perf_counter()
            batch_rows = rows[i:i+batch_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                batch_results = list(executor.map(lambda row: self.process_url(row["Domain"], selected_model), batch_rows))
            results.extend(batch_results)
            progress_bar.progress(min((i + batch_size) / len(rows), 1.0))
            status_text.text(f"Processing Batch {i // batch_size + 1} of {total_batches}")
            batch_end = time.perf_counter()
            elapsed = batch_end - batch_start
            timer_text.text(f"Batch {i // batch_size + 1} processed in {elapsed:.2f} seconds")
            interim_df = pd.DataFrame(results)
            if not interim_df.empty:
                self.components.display_results(interim_df)
        # Store results in session state for display
        st.session_state.results = df_input.assign(**{
            col: [result.get(col, "") for result in results]
            for col in ["Business Name", "Business Location",
                        "Keyword 1", "Keyword 2", "Keyword 3", "Keyword 4", "Keyword 5",
                        "Product/Service 1", "Product/Service 2", "Product/Service 3",
                        "Target Audience 1", "Target Audience 2", "Target Audience 3",
                        "Status", "Error"]
        })
        self.components.display_results(st.session_state.results)

    @timer
    def process_advanced_analysis(self, uploaded_file, gmb_check, no_of_pages, search_method, api_key, batch_size, max_workers):
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = uploaded_file.name.split('.')[-1]
        input_path = f"input/temp_{timestamp}.{ext}"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(input_path)
                except UnicodeDecodeError:
                    df = pd.read_csv(input_path, encoding='ISO-8859-1')
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(input_path)
            else:
                st.error("Unsupported file format. Please upload a CSV or Excel file.")
                return
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return
        required_columns = {"Domain", "Keyword 1", "Product/Service 1"}
        if not required_columns.issubset(set(df.columns)):
            st.error("Input file must have columns: Domain, Keyword 1, Product/Service 1")
            return
        results = []
        total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        status_text.text(f"Total Rows: {len(df)} | Processing in {total_batches} batches")
        for i in range(0, len(df), batch_size):
            batch_start = time.perf_counter()
            batch_rows = df.iloc[i:i+batch_size].to_dict(orient="records")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                batch_results = list(executor.map(
                    lambda row: self.process_row(row, search_method, api_key, gmb_check, no_of_pages),
                    batch_rows
                ))
            results.extend(batch_results)
            progress_bar.progress(min((i + batch_size) / len(df), 1.0))
            status_text.text(f"Processing Batch {i // batch_size + 1} of {total_batches}")
            interim_df = pd.DataFrame(results)
            if not interim_df.empty:
                self.components.display_results(interim_df)
        logging.debug("Advanced analysis completed.")
        # Store results in session state for display
        st.session_state.results = df.assign(**{
            col: [result.get(col, "") for result in results]
            for col in ["Keyword 1", "Product/Service 1", "Search Query",
                        "Top Competitor 1", "Serp Rank 1",
                        "Top Competitor 2", "Serp Rank 2",
                        "Top Competitor 3", "Serp Rank 3",
                        "GMB Status", "Error", "Status"]
        })
        self.components.display_results(st.session_state.results)

    def process_row(self, row, search_method, api_key, gmb_check, no_of_pages):
        logging.debug("Processing row: %s", row)
        try:
            domain = str(row.get("Domain", "")).strip()
            keyword = str(row.get("Keyword 1", "")).strip()
            product = str(row.get("Product/Service 1", "")).strip()
            if not domain:
                return {
                    "Domain": domain,
                    "Keyword 1": keyword,
                    "Product/Service 1": product,
                    "Search Query": "",
                    "Top Competitor 1": "",
                    "Serp Rank 1": "",
                    "Top Competitor 2": "",
                    "Serp Rank 2": "",
                    "Top Competitor 3": "",
                    "Serp Rank 3": "",
                    "GMB Status": "",
                    "Status": "error",
                    "Error": "Missing Domain"
                }
            search_query = keyword if keyword else product
            if not search_query:
                return {
                    "Domain": domain,
                    "Keyword 1": keyword,
                    "Product/Service 1": product,
                    "Search Query": "",
                    "Top Competitor 1": "",
                    "Serp Rank 1": "",
                    "Top Competitor 2": "",
                    "Serp Rank 2": "",
                    "Top Competitor 3": "",
                    "Serp Rank 3": "",
                    "GMB Status": "",
                    "Status": "error",
                    "Error": "No valid search query"
                }
            try:
                if search_method == "Serper.dev API" and api_key:
                    search_result = self.analytics.search_serper(search_query, api_key)
                else:
                    search_result = self.analytics.fetch_google_results(search_query, domain, pages=no_of_pages)
                if not search_result or (isinstance(search_result, dict) and "error" in search_result):
                    return {
                        "Domain": domain,
                        "Keyword 1": keyword,
                        "Product/Service 1": product,
                        "Search Query": search_query,
                        "Top Competitor 1": "",
                        "Serp Rank 1": "",
                        "Top Competitor 2": "",
                        "Serp Rank 2": "",
                        "Top Competitor 3": "",
                        "Serp Rank 3": "",
                        "GMB Status": "",
                        "Status": "error",
                        "Error": search_result.get("error", "No search results")
                    }
            except Exception as e:
                return {
                    "Domain": domain,
                    "Keyword 1": keyword,
                    "Product/Service 1": product,
                    "Search Query": search_query,
                    "Top Competitor 1": "",
                    "Serp Rank 1": "",
                    "Top Competitor 2": "",
                    "Serp Rank 2": "",
                    "Top Competitor 3": "",
                    "Serp Rank 3": "",
                    "GMB Status": "",
                    "Status": "error",
                    "Error": str(e)
                }
            competitors = self.analytics.clean_and_filter_urls(search_result, domain)
            if not competitors:
                return {
                    "Domain": domain,
                    "Keyword 1": keyword,
                    "Product/Service 1": product,
                    "Search Query": search_query,
                    "Top Competitor 1": "",
                    "Serp Rank 1": "",
                    "Top Competitor 2": "",
                    "Serp Rank 2": "",
                    "Top Competitor 3": "",
                    "Serp Rank 3": "",
                    "GMB Status": "",
                    "Status": "error",
                    "Error": "No valid competitors"
                }
            result = {
                "Domain": domain,
                "Keyword 1": keyword,
                "Product/Service 1": product,
                "Search Query": search_query,
                "GMB Status": ""
            }
            for i in range(3):
                if i < len(competitors):
                    result[f"Top Competitor {i+1}"] = competitors[i].get("link", "")
                    result[f"Serp Rank {i+1}"] = competitors[i].get("position", "")
                else:
                    result[f"Top Competitor {i+1}"] = ""
                    result[f"Serp Rank {i+1}"] = ""
            if gmb_check:
                gmb_result = self.analytics.check_gmb_listing(keyword, domain)
                result["GMB Status"] = "Found" if gmb_result.get("exists") else "Not Found"
            else:
                result["GMB Status"] = "Not Checked"
            result["Status"] = "success"
            result["Error"] = ""
            return result
        except Exception as e:
            return {
                "Domain": domain,
                "Keyword 1": keyword,
                "Product/Service 1": product,
                "Search Query": "",
                "Top Competitor 1": "",
                "Serp Rank 1": "",
                "Top Competitor 2": "",
                "Serp Rank 2": "",
                "Top Competitor 3": "",
                "Serp Rank 3": "",
                "GMB Status": "",
                "Status": "error",
                "Error": str(e)
            }

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
            business_name = analysis.get('business_name', '')
            location = analysis.get('location', '')
            keywords = analysis.get('keywords', '')
            product_services = analysis.get('products_services', '')
            target_audiences = analysis.get('target_audience', '')
            return {
                "Business Name": business_name,
                "Business Location": location,
                "Keyword 1": keywords,
                "Product/Service 1": product_services,
                "Target Audience 1": target_audiences,
                "Status": "success",
                "Error": ""
            }
        except Exception as e:
            return {
                "Business Name": "",
                "Business Location": "",
                "Keyword 1": "",
                "Product/Service 1": "",
                "Target Audience 1": "",
                "Status": "error",
                "Error": str(e)
            }

if __name__ == "__main__":
    app = WebApp()
    app.run()
