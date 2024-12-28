# src/web/app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from src.core.scraper import WebScraper
from src.core.content_analyzer import ContentAnalyzer
from src.core.data_processer import DataProcessor
from src.utils.components import Components

import sys

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class WebApp:
    def __init__(self):
        self.init_session()
        self.components = Components()
        self.scraper = WebScraper()
        self.processor = DataProcessor()
        self.analyzer = ContentAnalyzer()

    def init_session(self):
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'results' not in st.session_state:
            st.session_state.results = None

    def run(self):
        st.set_page_config(page_title="Website Analysis Tool", layout="wide")
        
        if not st.session_state.authenticated:
            self.components.show_login()
        else:
            self.show_main_page()

    def show_main_page(self):
        st.title("🌐 Website Analysis Tool")
        
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

        uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")
            if st.button("Start Analysis"):
                self.process_file(uploaded_file)

    def process_file(self, uploaded_file):
        try:
            # Create directories
            os.makedirs('input', exist_ok=True)
            os.makedirs('output/analysis', exist_ok=True)

            progress_bar = st.progress(0)
            status = st.empty()
            
            # Save and process file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            input_path = f"input/temp_{timestamp}.xlsx"
            with open(input_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            urls = self.processor.read_excel_to_url(input_path)
            results = []

            for i, url in enumerate(urls):
                status.text(f"Processing {url}")
                progress = (i + 1) / len(urls)
                progress_bar.progress(progress)
                
                try:
                    clean_url = self.processor.clean_url(url)
                    scraped_data = self.scraper.scrape_website(clean_url)
                    analysis = self.analyzer.analyze_with_ollama(
                        scraped_data['content'],
                        clean_url
                    )
                    
                    results.append({
                        'url': url,
                        'status': 'success',
                        **analysis
                    })
                except Exception as e:
                    results.append({
                        'url': url,
                        'status': 'error',
                        'error': str(e)
                    })

            df = pd.DataFrame(results)
            output_file = f"output/analysis/results_{timestamp}.csv"
            df.to_csv(output_file, index=False)
            
            self.components.display_results(df)
            os.remove(input_path)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    app = WebApp()
    app.run()
