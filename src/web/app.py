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
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Timer decorator to measure function runtime.
def timer(func):
    """Decorator to measure the runtime of functions."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # High-resolution timer.
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        logging.info("Function %s took %.2f seconds", func.__name__, elapsed)
        st.write(f"Function **{func.__name__}** took **{elapsed:.2f}** seconds to complete.")
        return result
    return wrapper

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Adjust log level as needed
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
        # Force light mode and apply custom CSS to style buttons.
        st.set_page_config(page_title="Corporate Ranking AI", layout="wide", page_icon="assets/logo.jpg")
        st.markdown(
            """
            <style>
            body { background-color: #ffffff; }
            .stButton>button { background-color: #4CAF50; color: white; border: none; }
            </style>
            """, unsafe_allow_html=True)
        if not st.session_state.authenticated:
            self.components.show_login(auth_manager=self.auth_manager)
        else:
            self.show_main_page()

    def show_main_page(self):
        col1, col2 = st.columns([1, 8])
        with col1:
            st.image("assets/logo.jpg", width=100)
        with col2:
            st.title("Corporate Ranking AI")
        # Updated tab names.
        tabs = st.tabs(["AI-POWERED DATA EXTRACTOR", "COMPETITIVE INSIGHTS"])
        with tabs[0]:
            self.ai_based_extractor()
        with tabs[1]:
            self.competitive_insights()

    def ai_based_extractor(self):
        st.markdown("""
          **DATA EXTRACTION FACTORS**

          · **Business Name**  
          · **Business Location**  
          · **Keywords (5)**  
          · **Product/Service (3)**  
          · **Target Audience (3)**  

          · **Input Format:** (CSV/XLS/XLSX) with must have website’s name as input information (Heading of the column must be **Domain**).  
          · **Output Format:** XLSX/CSV
        """)

        uploader_cols = st.columns(2)
        with uploader_cols[0]:
            uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
        with uploader_cols[1]:
             st.session_state.selected_model = st.selectbox("Select Model", ["llama3.1:8b"])
             if 'selected_model' not in st.session_state:
                st.session_state.selected_model = "llama3.1:8b"
          
        if uploaded_file:
            if st.button("Start Data Extraction"):
                self.process_basic_analysis(uploaded_file)

    def competitive_insights(self):
        st.markdown("""
          **COMPETITIVE ANALYSIS FACTORS**

          · Top Competitor 1 (Website Only)  
          · Top Competitor 2 (Website Only)  
          · Top Competitor 1 SERP Rank  
          · Top Competitor 2 SERP Rank  

          · **Input Format:** (CSV/XLS/XLSX) with must have Website’s name, **Keyword 1**, **Product/Service 1** as input information (Heading of the column must be **Domain**, **Keyword 1**, **Product/Service 1**).  
          · **Output Format:** XLSX/CSV
        """)
        # GMB checkbox and radio button for SERP pages.
        gmb_cols = st.columns(2)
        with gmb_cols[0]:
            gmb_check = st.checkbox("Check Google My Business (GMB)")
        with gmb_cols[1]:
            no_of_pages = st.radio("Number of SERP Pages", options=[1, 2])
        # Three-column layout for search method, API key input, and submit button.
        cols = st.columns(3)
        with cols[0]:
            uploaded_file = st.file_uploader("Upload Competitive Analysis Input File (CSV/XLS/XLSX)", type=['csv', 'xlsx', 'xls'])
        with cols[1]:
            search_method = st.selectbox("Select Search Method", ("Serper.dev API", "Basic Google Search"))
        with cols[2]:
            api_key_input = None
            if search_method == "Basic Google Search":
                st.info("Basic Google Search selected. No API key required.")
            elif search_method == "Serper.dev API":
                if "serper_api" not in st.session_state:
                    api_key_input = st.text_input("Enter your Serper.dev API Key", type="password")
                else:
                    st.write("API Key submitted already.")
                    api_key_input = st.text_input("To update your Serper.dev API Key", type="password")
        
        if st.button("Submit API Key"):
             st.session_state.serper_api = api_key_input
             st.success("API Key stored for this session.")
             
        api_key = st.session_state.get("serper_api", None)

        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_input = pd.read_csv(uploaded_file)
                else:
                    df_input = pd.read_excel(uploaded_file)
            except Exception as e:
                st.error("Error reading the input file.")
                return
            required_columns = {"Domain", "Keyword 1", "Product/Service 1"}
            if not required_columns.issubset(set(df_input.columns)):
                st.error("Input file must have columns: Domain, Keyword 1, Product/Service 1")
                return
            if st.button("Start Analysis"):
                self.process_advanced_analysis(uploaded_file, gmb_check, no_of_pages, search_method, api_key)
        if st.session_state.get("results") is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            st.write("### Download Competitive Analysis Results")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.results.to_excel(writer, sheet_name='Results', index=False)
            output.seek(0)
            st.download_button(
                label="Download Excel File",
                data=output,
                file_name="competitive_analysis_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    @timer
    def process_basic_analysis(self, uploaded_file):
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
        batch_size = 40
        total_batches = len(rows) // batch_size + (1 if len(rows) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        timer_text = st.empty()
        status_text.text(f"Total Rows: {len(rows)} | Processing in {total_batches} batches")
        selected_model = st.session_state.selected_model

        for i in range(0, len(rows), batch_size):
            batch_start = time.perf_counter()
            batch_rows = rows[i:i+batch_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                batch_results = list(executor.map(lambda row: self.process_url(row["Domain"], selected_model), batch_rows))
            results.extend(batch_results)
            progress_bar.progress(min((i + batch_size) / len(rows), 1.0))
            status_text.text(f"Processing Batch {i // batch_size + 1} of {total_batches}")
            batch_end = time.perf_counter()
            elapsed = batch_end - batch_start
            timer_text.text(f"Batch {i // batch_size + 1} processed in {elapsed:.2f} seconds")
            
            # Update display after each batch
            interim_df = pd.DataFrame(results)
            if not interim_df.empty:
                self.components.display_results(interim_df)
        
        # Final merge (if needed) and download button creation
        new_columns = ["Business Name", "Business Location",
                      "Keyword 1", "Keyword 2", "Keyword 3", "Keyword 4", "Keyword 5",
                      "Product/Service 1", "Product/Service 2", "Product/Service 3",
                      "Target Audience 1", "Target Audience 2", "Target Audience 3",
                      "Status", "Error"]
        df_output = df_input.copy()
        for col in new_columns:
            df_output[col] = ""
        for idx, result in enumerate(results):
            for col in new_columns:
                df_output.at[idx, col] = result.get(col, "")
        st.session_state.results = df_output
        self.components.display_results(df_output)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_output.to_excel(writer, sheet_name='Results', index=False)
        output.seek(0)
        st.download_button(
            label="Download Analysis Results (Excel)",
            data=output,
            file_name="basic_analysis_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


    @timer
    def process_advanced_analysis(self, uploaded_file, gmb_check, no_of_pages, search_method, api_key):
        os.makedirs('input', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = f"input/temp_{timestamp}.{uploaded_file.name.split('.')[-1]}"
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(input_path)
                except UnicodeDecodeError as e:
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
        batch_size = 100
        total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        status_text.text(f"Total Rows: {len(df)} | Processing in {total_batches} batches")
        for i in range(0, len(df), batch_size):
            batch_start = time.perf_counter()
            batch_rows = df.iloc[i:i+batch_size].to_dict(orient="records")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                batch_results = list(executor.map(
                    lambda row: self.process_row(row, search_method, api_key, gmb_check, no_of_pages),
                    batch_rows
                ))
            results.extend(batch_results)
            progress_bar.progress(min((i + batch_size) / len(df), 1.0))
            status_text.text(f"Processing Batch {i // batch_size + 1} of {total_batches}")
            
            # Display interim results after each batch
            interim_df = pd.DataFrame(results)
            if not interim_df.empty:
                self.components.display_results(interim_df)
        logging.debug("Advanced analysis completed.")
        new_columns = ["Keyword 1", "Product/Service 1", "Search Query",
                      "Top Competitor 1", "Serp Rank 1",
                      "Top Competitor 2", "Serp Rank 2",
                      "Top Competitor 3", "Serp Rank 3",
                      "GMB Status", "Error"]
        df_output = df.copy()
        for col in new_columns:
            df_output[col] = ""
        for idx, result in enumerate(results):
            for col in new_columns:
                df_output.at[idx, col] = result.get(col, "")
        st.session_state.results = df_output
        self.components.display_results(df_output)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_output.to_excel(writer, sheet_name='Results', index=False)
        output.seek(0)
        st.download_button(
            label="Download Competitive Analysis Results (Excel)",
            data=output,
            file_name="competitive_analysis_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

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
        """
        Processes a single URL for basic extraction.
        Returns a dictionary with keys:
        Domain, Business Name, Business Location, Keyword 1-5, 
        Product/Service 1-3, Target Audience 1-3, Status, Error.
        """
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
            if not keywords and not product_services:
                logging.warning("Missing keywords and products for URL %s", url)
                return {
                    "Domain": url,
                    "Business Name": "",
                    "Business Location": "",
                    "Keyword 1": "", "Keyword 2": "", "Keyword 3": "", "Keyword 4": "", "Keyword 5": "",
                    "Product/Service 1": "", "Product/Service 2": "", "Product/Service 3": "",
                    "Target Audience 1": "", "Target Audience 2": "", "Target Audience 3": "",
                    "Status": "error",
                    "Error": "Missing keywords and products"
                }
            result = {
                "Domain": url,
                "Business Name": business_name,
                "Business Location": location,
                "Status": "success"
            }
            keyword_list = [k.strip() for k in keywords.split(',')] if keywords else []
            for i in range(5):
                result[f"Keyword {i+1}"] = keyword_list[i] if i < len(keyword_list) else ""
            product_services_list = [p.strip() for p in product_services.split(',')] if product_services else []
            for i in range(3):
                result[f"Product/Service {i+1}"] = product_services_list[i] if i < len(product_services_list) else ""
            target_audience_list = [t.strip() for t in target_audiences.split(',')] if target_audiences else []
            for i in range(3):
                result[f"Target Audience {i+1}"] = target_audience_list[i] if i < len(target_audience_list) else ""
            return result
        except Exception as e:
            logging.error("Error processing URL %s: %s", url, e)
            return {
                "Domain": url,
                "Business Name": "",
                "Business Location": "",
                "Keyword 1": "", "Keyword 2": "", "Keyword 3": "", "Keyword 4": "", "Keyword 5": "",
                "Product/Service 1": "", "Product/Service 2": "", "Product/Service 3": "",
                "Target Audience 1": "", "Target Audience 2": "", "Target Audience 3": "",
                "Status": "error",
                "Error": str(e)
            }


if __name__ == "__main__":
    logging.debug("Starting WebApp.")
    app = WebApp()
    app.run()
