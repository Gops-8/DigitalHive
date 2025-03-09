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
import re
import asyncio

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

# Ensure the logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# --- Logging with IST Timestamps ---
import time
class ISTFormatter(logging.Formatter):
    def converter(self, timestamp):
        return time.gmtime(timestamp + 19800)  # IST offset: 5.5 hours

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return s

formatter = ISTFormatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler("logs/debug.log")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logging.basicConfig(
    level=logging.ERROR,
    handlers=[file_handler, stream_handler]
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.core.scraper import WebScraper
from src.core.content_analyzer import ContentAnalyzer
from src.core.data_processer import DataProcessor
from src.utils.components import Components
from src.utils.auth import AuthManager
from src.core.advanced_analytics import AdvancedAnalytics
from src.utils.cache import AnalysisCache

def fix_keyword_spacing(keyword: str) -> str:
    keyword = keyword.replace('_', ' ')
    keyword = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', keyword)
    return keyword.strip()

# --------------------- WebApp Class (UI) ---------------------
class WebApp:
    def __init__(self):
        self.init_session()
        self.components = Components()
        self.scraper = WebScraper()
        self.processor = DataProcessor()
        self.auth_manager = AuthManager()
        # Initialize AdvancedAnalytics with competitor caching folder.
        self.analytics = AdvancedAnalytics()
        # Create separate cache instances:
        self.cache_extractor = AnalysisCache(cache_dir="output/cache_extractor")
        self.cache_competitor = AnalysisCache(cache_dir="output/cache_competitor")

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
            [data-testid="stAppViewContainer"] {
                background-image: linear-gradient(135deg, #ffffff,rgb(211, 211, 211)) !important;
                background-size: cover !important;
                background-position: center !important;
            }
            div.stButton > button {
                background-color: #4CAF50 !important;
                color: white !important;
                border: none !important;
                padding: 8px 16px !important;
                font-size: 14px !important;
                cursor: pointer !important;
            }
            div.stButton > button:hover {
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
          · **Output Format:** XLSX/CSV
        """
        )
        col1, col2 = st.columns([2, 2])
        with col1:
            st.subheader(" Upload File and Model Selection ")
            uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
            st.session_state.selected_model = st.selectbox(
                "Select Model",
                ["llama3.1:8b", "llama3.3:70b", "qwen2.5:14b", "qwen2.5:32b", "qwen2.5:7b", "deepseek-r1:32b", "olmo2:13b"]
            )
        with col2:
            st.subheader(" Choose Run Configuration ")
            col3,col4 = st.columns([1,1])
            with col3:
                max_workers_options = [8, 16, 20, 24, 25, 28, 50]
                selected_max_workers = st.selectbox("Select Max Workers", options=max_workers_options)
                cache_option = st.radio("Reference from Cache", options=["Include", "Exclude"], index=1, key="cache_ref_extractor")
            with col4:
                base_batch_sizes = [8, 16, 24, 25, 28, 32, 40, 48, 50, 56, 64, 72, 75, 80, 84, 96, 100, 112, 120, 140]
                selected_batch_size = st.selectbox("Select Batch Size", options=base_batch_sizes)
                file_store_option = st.radio("Save intermediate Files", options=["Save", "Do Not Save"], index=1, key="file_save_ref")
            # Cache Reference Option for AI extractor
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
          · Top Competitor 3 SERP Rank
          · **Domain Rank:** Position if the origin URL appears in the search results; otherwise, “not ranked.”

          · **Input Format:** (CSV/XLS/XLSX) with the columns **Domain**, **Keyword 1**, **Product/Service 1**.
          · **Output Format:** Displayed on screen
        """
        )
        row1 = st.columns([1.7, 2.2, 0.8])
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
        row2 = st.columns([2, 2])
        with row2[0]:
            uploaded_file = st.file_uploader("Upload Competitive Analysis Input File", type=['csv', 'xlsx', 'xls'])
            gmb_check = st.checkbox("Check Google My Business (GMB)")

        with row2[1]:
            row21 = st.columns([1, 1])
            with row21[0]:
                 max_workers_options = [8, 16, 24, 25, 28, 32]
                 comp_selected_max_workers = st.selectbox("Select Max Workers", options=max_workers_options, key="comp_workers")
            with row21[1]:
                base_batch_sizes = [8, 16, 24, 25, 28, 32, 40, 48, 50, 56, 64, 72, 75, 80, 84, 96, 100, 112, 120, 140]
                comp_selected_batch_size = st.selectbox("Select Batch Size", options=base_batch_sizes, key="comp_batch")
            # Cache Reference Option for Competitive Analysis
            row20 = st.columns([1, 1])
            with row20[0]:
                cache_option_comp = st.radio("Reference from Cache", options=["Include", "Exclude"], index=0, key="cache_ref_comp")
            with row20[1]:
                no_of_pages = st.radio("Number of SERP Pages", options=[1, 2])


        st.markdown('<div class="small-button">', unsafe_allow_html=True)
        if uploaded_file and st.button("Start Analysis", key="start_comp_analysis"):
            self.process_advanced_analysis(
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
        st.write("Processing AI Based Data Extraction")
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
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        timer_text = st.empty()
        total_batches = len(rows) // batch_size + (1 if len(rows) % batch_size > 0 else 0)
        status_text.text(f"Total Rows: {len(rows)} | Processing in {total_batches} batches")
        selected_model = st.session_state.selected_model

        async def process_batches():
            results = []
            TIMEOUT_SECONDS = 240
            for i in range(0, len(rows), batch_size):
                current_batch = i // batch_size + 1
                # Show batch status immediately before processing starts
                status_text.text(f"Processing Batch {current_batch} of {total_batches} from {len(rows)} datas ")

                batch_start = time.perf_counter()
                batch_rows = rows[i:i+batch_size]
                tasks = []
                for row in batch_rows:
                    task = asyncio.wait_for(
                        asyncio.to_thread(self.process_url, row["Domain"], selected_model, row.get("Email ID", "")),
                        timeout=TIMEOUT_SECONDS
                    )
                    tasks.append(task)
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for idx, result in enumerate(batch_results):
                    if isinstance(result, asyncio.TimeoutError):
                        logging.error("Timeout processing URL: %s", batch_rows[idx].get("Domain"))
                        # Return a complete dict with all expected keys
                        result = {
                            "Domain": batch_rows[idx].get("Domain", ""),
                            "Email ID": batch_rows[idx].get("Email ID", ""),
                            "Business Name": "",
                            "Business Location": "",
                            "Keyword 1": "",
                            "Keyword 2": "",
                            "Keyword 3": "",
                            "Keyword 4": "",
                            "Keyword 5": "",
                            "Product/Service 1": "",
                            "Product/Service 2": "",
                            "Product/Service 3": "",
                            "Target Audience 1": "",
                            "Target Audience 2": "",
                            "Target Audience 3": "",
                            "Status": "error",
                            "Error": f"Timeout after {TIMEOUT_SECONDS} seconds"
                        }
                    elif isinstance(result, Exception):
                        logging.error("Error processing URL %s: %s", batch_rows[idx].get("Domain"), str(result))
                        result = {
                            "Domain": batch_rows[idx].get("Domain", ""),
                            "Email ID": batch_rows[idx].get("Email ID", ""),
                            "Business Name": "",
                            "Business Location": "",
                            "Keyword 1": "",
                            "Keyword 2": "",
                            "Keyword 3": "",
                            "Keyword 4": "",
                            "Keyword 5": "",
                            "Product/Service 1": "",
                            "Product/Service 2": "",
                            "Product/Service 3": "",
                            "Target Audience 1": "",
                            "Target Audience 2": "",
                            "Target Audience 3": "",
                            "Status": "error",
                            "Error": str(result)
                        }
                    results.append(result)
                progress_bar.progress(min((i + batch_size) / len(rows), 1.0))
                interim_df = pd.DataFrame(results)
                timer_text.text(f"Batch {current_batch} processed in {time.perf_counter() - batch_start:.2f} seconds")
                if not interim_df.empty:
                    self.components.display_results(interim_df)
                    save_file = st.session_state.get("file_save_ref", "Save") == "Save"
                    if save_file:
                        if (current_batch%10==0) and (current_batch>0):
                            interim_df.index = interim_df.index + 1
                            interim_df.to_excel(f"output/analysis/interim_{timestamp}_{current_batch}.xlsx",index=True)
            return results

        results = asyncio.run(process_batches())
        st.session_state.results = df_input.assign(**{
            col: [result.get(col, "") for result in results]
            for col in ["Business Name", "Business Location",
                        "Keyword 1", "Keyword 2", "Keyword 3", "Keyword 4", "Keyword 5",
                        "Product/Service 1", "Product/Service 2", "Product/Service 3",
                        "Target Audience 1", "Target Audience 2", "Target Audience 3",
                        "Status", "Error"]
        })
        if "Email ID" in df_input.columns:
            st.session_state.results["Email ID"] = df_input["Email ID"]
        self.components.display_results(st.session_state.results)
        WebApp.download_results_excel_static(st.session_state.results, timestamp)

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

        progress_bar = st.progress(0.0)
        status_text = st.empty()
        timer_text = st.empty()
        total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
        status_text.text(f"Total Rows: {len(df)} | Processing in {total_batches} batches")

        with st.spinner("Processing Competitor  Analyzer..."):
            for i in range(0, len(df), batch_size):
                batch_start = time.perf_counter()
                batch_rows = df.iloc[i:i+batch_size].to_dict(orient="records")
                batch_results = []
                status_text.text(f"Processing Batch {i // batch_size + 1} of {total_batches}")
                for row in batch_rows:
                    rec_start = time.perf_counter()
                    res = self.process_row(row, search_method, api_key, gmb_check, no_of_pages)
                    rec_elapsed = time.perf_counter() - rec_start
                    logging.debug("Processed record for URL %s in advanced analysis in %.2f seconds", row.get("Domain", "N/A"), rec_elapsed)
                    batch_results.append(res)
                results.extend(batch_results)
                progress_bar.progress(min((i + batch_size) / len(df), 1.0))

                batch_end = time.perf_counter()
                elapsed = batch_end - batch_start

                logging.debug("Batch %d processed in %.2f seconds", i // batch_size + 1, elapsed)
                interim_df = pd.DataFrame(results)
                if not interim_df.empty:
                    self.components.display_results(interim_df)

        logging.debug("Advanced analysis completed.")
        st.session_state.results = df.assign(**{
            col: [result.get(col, "") for result in results]
            for col in ["Keyword 1", "Product/Service 1", "Search Query",
                        "Top Competitor 1", "Serp Rank 1",
                        "Top Competitor 2", "Serp Rank 2",
                        "Top Competitor 3", "Serp Rank 3",
                        "Domain Rank",
                        "GMB Status", "Error", "Status"]
        })
        self.components.display_results(st.session_state.results)
        WebApp.download_results_excel_static(st.session_state.results, timestamp)

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
                    "Domain Rank": "not ranked",
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
                    "Domain Rank": "not ranked",
                    "GMB Status": "",
                    "Status": "error",
                    "Error": "No valid search query"
                }
            # Decide whether to use cache based on the radio button.
            use_cache = st.session_state.get("cache_ref_comp", "Include") == "Include"
            if search_method == "Serper.dev API" and api_key:
                raw_search_result = self.analytics.search_serper(search_query, api_key, use_cache=use_cache)
            else:
                raw_search_result = self.analytics.fetch_google_results(search_query, domain, pages=no_of_pages)
            if not raw_search_result or (isinstance(raw_search_result, dict) and "error" in raw_search_result):
                result = {
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
                    "Domain Rank": "not ranked",
                    "GMB Status": "",
                    "Status": "error",
                    "Error": raw_search_result.get("error", "No search results")
                }
                return result

            # Process raw search result (which is now cached only for the raw query) to compute competitor analysis.
            competitors = self.analytics.clean_and_filter_urls(raw_search_result, domain)

            # Compute Domain Rank by checking raw search result for the origin domain.
            domain_rank = "not ranked"
            from urllib.parse import urlparse
            parsed_origin = urlparse(domain)
            origin_netloc = parsed_origin.netloc.lower() if parsed_origin.netloc else domain.lower()
            if isinstance(raw_search_result, list):
                for entry in raw_search_result:
                    if isinstance(entry, dict):
                        competitor_link = entry.get("link", "")
                        competitor_position = entry.get("position", "not ranked")
                    elif isinstance(entry, str):
                        competitor_link = entry
                        competitor_position = "not ranked"
                    else:
                        continue
                    parsed_comp = urlparse(competitor_link)
                    competitor_netloc = parsed_comp.netloc.lower() if parsed_comp.netloc else competitor_link.lower()
                    if origin_netloc in competitor_netloc or competitor_netloc in origin_netloc:
                        domain_rank = competitor_position
                        break

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
                    position = competitors[i].get("position")
                    result[f"Serp Rank {i+1}"] = position if position is not None else "not ranked"
                else:
                    result[f"Top Competitor {i+1}"] = ""
                    result[f"Serp Rank {i+1}"] = "not ranked"
            result["Domain Rank"] = domain_rank
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
                "Domain Rank": "not ranked",
                "GMB Status": "",
                "Status": "error",
                "Error": str(e)
            }

    def process_url(self, url, model, email_id=""):
        logging.debug("Processing URL: %s with model: %s", url, model)
        try:
            clean_url = self.processor.clean_url(url)
            # Check extractor cache option
            use_cache = st.session_state.get("cache_ref_extractor", "Include") == "Include"
            if use_cache:
                cached_data = self.cache_extractor.get(clean_url)
            else:
                cached_data = None
            if not cached_data:
                scraped_data = self.scraper.scrape_website(clean_url)
                self.cache_extractor.set(clean_url, scraped_data)
                logging.debug("Scraped data for URL %s", clean_url)
            else:
                scraped_data = cached_data
                logging.debug("Using cached data for URL %s", clean_url)

            analyzer = ContentAnalyzer(model=model)
            analysis = analyzer.analyze_with_ollama(scraped_data['content'], clean_url)
            logging.debug("Analysis result for URL %s: %s", clean_url, analysis)

            business_name = analysis.get('business_name', '')
            location = analysis.get('location', '')

            keywords = analysis.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(',')]
            US_STATES = {"AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                         "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                         "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                         "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                         "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"}
            keywords = [fix_keyword_spacing(kw) for kw in keywords if kw.upper() not in US_STATES]
            keywords = (keywords + [""] * 5)[:5]

            product_services = analysis.get('products_services', [])
            if isinstance(product_services, str):
                product_services = [ps.strip() for ps in product_services.split(',')]
            product_services = (product_services + [""] * 3)[:3]

            target_audiences = analysis.get('target_audience', [])
            if isinstance(target_audiences, str):
                target_audiences = [ta.strip() for ta in target_audiences.split(',')]
            target_audiences = (target_audiences + [""] * 3)[:3]

            result = {}
            result["Domain"] = url
            result["Email ID"] = email_id
            result["Business Name"] = business_name
            result["Business Location"] = location

            for i, kw in enumerate(keywords, start=1):
                result[f"Keyword {i}"] = kw

            for i, ps in enumerate(product_services, start=1):
                result[f"Product/Service {i}"] = ps

            for i, ta in enumerate(target_audiences, start=1):
                result[f"Target Audience {i}"] = ta

            result["Status"] = "success"
            result["Error"] = ""

            return result

        except Exception as e:
            return {
                "Domain": url,
                "Email ID": email_id,
                "Business Name": "",
                "Business Location": "",
                "Status": "error",
                "Error": str(e)
            }

    @staticmethod
    @st.fragment
    def download_results_excel_static(results, timestamp):
        if results is not None:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                results.to_excel(writer, index=False)
            buffer.seek(0)
            st.download_button(
                label="Download Results as Excel",
                data=buffer,
                file_name=f"results_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    app = WebApp()
    app.run()
