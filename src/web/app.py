import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.core.scraper import WebScraper
from src.core.content_analyzer import ContentAnalyzer
from src.core.data_processer import DataProcessor
from src.utils.components import Components
from src.utils.auth import AuthManager
from src.core.advanced_analytics import AdvancedAnalytics


class WebApp:
    def __init__(self):
        self.init_session()
        self.components = Components()
        self.scraper = WebScraper()
        self.processor = DataProcessor()
        self.analyzer = ContentAnalyzer()
        self.auth_manager = AuthManager()
        self.analytics = AdvancedAnalytics()

    def init_session(self):
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'results' not in st.session_state:
            st.session_state.results = None

    def run(self):
        st.set_page_config(page_title="Digital-Hive", layout="wide")
        
        if not st.session_state.authenticated:
            self.components.show_login(auth_manager=self.auth_manager)
        else:
            self.show_main_page()

    def show_main_page(self):
        st.title("🌐 Digital-Hive 🌐 ")
        
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

        uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
        advanced_analytics = st.checkbox("Advanced Analytics", help="Include GMB check, top competitors, and non-indexed pages in the results")

        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")
            if st.button("Start Analysis"):
                st.session_state.processing = True
                self.process_file(uploaded_file, advanced_analytics)

        # Display results only if available and processing is complete
        if not st.session_state.processing and st.session_state.results is not None:
            self.components.display_results(st.session_state.results)
    
    def process_file(self, uploaded_file, advanced_analytics):
          try:
              os.makedirs('input', exist_ok=True)
              os.makedirs('output/analysis', exist_ok=True)

              progress_bar = st.progress(0)
              status = st.empty()
              percent_complete = st.empty()
              
              timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
              input_path = f"input/temp_{timestamp}.xlsx"
              with open(input_path, 'wb') as f:
                  f.write(uploaded_file.getbuffer())
              
              urls = self.processor.read_excel_to_url(input_path)
              results = []
              batch_size = 1000
              total_batches = (len(urls) + batch_size - 1) // batch_size

              for batch_number in range(total_batches):
                  if not st.session_state.processing:
                      break  # Stop processing if flagged

                  # Extract current batch
                  start_index = batch_number * batch_size
                  end_index = min(start_index + batch_size, len(urls))
                  batch_urls = urls[start_index:end_index]

                  st.write(f"Processing Batch {batch_number + 1}/{total_batches}...")

                  for i, url in enumerate(batch_urls):
                      status.text(f"Processing URL: {url}")
                      progress = ((batch_number * batch_size + i + 1) / len(urls))
                      progress_bar.progress(progress)
                      percent_complete.text(f"Batch {batch_number + 1}/{total_batches}: {int(progress * 100)}% Complete")

                      try:
                          # Process URL
                          clean_url = self.processor.clean_url(url)
                          scraped_data = self.scraper.scrape_website(clean_url)
                          analysis = self.analyzer.analyze_with_ollama(scraped_data['content'], clean_url)

                          # Extract location and product for advanced analytics
                          location = analysis.get('location', '')
                          keywords = analysis.get('keywords', [])
                          if not keywords:
                              results.append({
                                  'url': url,
                                  'status': 'partial error',
                                  'error': 'No keywords found',
                                  'top_competitors': '',
                                  'gmb_setup': '',
                                  'business_name': '',
                                  'non_indexed_pages': ''
                              })
                              continue
                          
                          top_key = keywords[0]
                          
                          result = {
                              'url': url,
                              'status': 'success',
                              **analysis
                          }

                          if advanced_analytics:
                              try:
                                  top_competitors = self.analytics.find_top_competitors(top_key, location, clean_url, pages=1)
                                  gmb_setup, business_name = self.analytics.check_gmb_setup(clean_url)
                                  non_indexed_pages = self.analytics.count_non_indexed_pages(clean_url)

                                  result.update({
                                      'top_competitors': top_competitors,
                                      'gmb_setup': gmb_setup,
                                      'business_name': business_name,
                                      'non_indexed_pages': non_indexed_pages,
                                  })
                              except Exception as e:
                                  result.update({
                                      'top_competitors': '',
                                      'gmb_setup': '',
                                      'business_name': '',
                                      'non_indexed_pages': '',
                                      'status': 'partial error',
                                      'error': str(e)
                                  })

                          results.append(result)
                      
                      except Exception as e:
                          results.append({
                              'url': url,
                              'status': 'error',
                              'error': str(e),
                              'top_competitors': '',
                              'gmb_setup': '',
                              'business_name': '',
                              'non_indexed_pages': ''
                          })

                  # Save intermediate results after each batch
                  df = pd.DataFrame(results)
                  st.session_state.results = df

                  # Display results so far
                  self.components.display_results(df)

              # Save final results to a CSV file
              output_file = f"output/analysis/results_{timestamp}.csv"
              df.to_csv(output_file, index=False)

              # Reset processing state
              st.session_state.processing = False

          except Exception as e:
              st.error(f"Error: {str(e)}")
              st.session_state.processing = False



if __name__ == "__main__":
    app = WebApp()
    app.run()
