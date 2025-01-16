import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
from time import time
# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

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
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'results' not in st.session_state:
            st.session_state.results = None

    def run(self):
        
        
        if not st.session_state.authenticated:
            st.set_page_config(page_title="Corporate Ranking AI",layout="centered",page_icon="assets/logo.jpg")
            self.components.show_login(auth_manager=self.auth_manager)
            
        else:
            st.set_page_config(page_title="Corporate Ranking AI",layout="wide",page_icon="assets/logo.jpg")
            self.show_main_page()

    def show_main_page(self):
        # st.image("assets/logo.jpg", width=200)
        # st.title("Corporate Ranking AI ")
        # Create two columns for layout
        col1, col2 = st.columns([1, 6])  # Adjust column widths as needed

        with col1:
            st.image("assets/logo.jpg", width=150)  # Replace with your logo file path
        with col2:
            st.title("Corporate Ranking AI")

        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

        uploaded_file = st.file_uploader("Upload Excel file with URLs", type=['xlsx', 'xls'])
        debug_mode = st.checkbox("Enable Debug Mode", help="Show detailed logs during execution")
        # advanced_analytics = st.checkbox("Advanced Analytics", help="Include GMB check, top competitors, and non-indexed pages in the results")
        features = {
            "basic": st.checkbox("Basic Features (keywords, business name, target audience, product and services),",value=True),
            "top_competitor": st.checkbox("Top Competitors"),
            "gmb": st.checkbox("Check Google My Business"),
            "non_index_pages": st.checkbox("Count Non-Indexed Pages")
          }
        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")
   
            if st.button("Start Analysis"):
                st.session_state.processing = True
                self.process_file(uploaded_file, features,debug_mode)

        # Display results only if available and processing is complete
        if not st.session_state.processing and st.session_state.results is not None:
            self.components.display_results(st.session_state.results)
    
    def process_file(self, uploaded_file, features,debug_mode):
          try:
              os.makedirs('input', exist_ok=True)
              os.makedirs('output/analysis', exist_ok=True)
              os.makedirs('output/debug_logs',exist_ok=True)
              start_time=time()
              progress_bar = st.progress(0)
              status = st.empty()
              percent_complete = st.empty()
              log_window = st.empty() if debug_mode else None
              
              timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
              input_path = f"input/temp_{timestamp}.xlsx"
              with open(input_path, 'wb') as f:
                  f.write(uploaded_file.getbuffer())
              
              urls = self.processor.read_excel_to_url(input_path)
              results = []
              batch_size = 100
              total_batches = (len(urls) + batch_size - 1) // batch_size
              debug_logs=f'----------------------- DEBUG LOGS : RUN on {timestamp}----------------------- \n\n\n'
              for batch_number in range(total_batches):
                  if not st.session_state.processing:
                      break  # Stop processing if flagged
                  batch_results=[]
                  # Extract current batch
                  start_index = batch_number * batch_size
                  end_index = min(start_index + batch_size, len(urls))
                  batch_urls = urls[start_index:end_index]

                  st.write(f"Processing Batch {batch_number + 1}/{total_batches}...")
                  
                  for i, url in enumerate(batch_urls):
                      url_start_time = time()
                      status.text(f"Processing {start_index+i+1}/{len(urls)} URL: {url}")
                      progress = ((batch_number * batch_size + i + 1) / len(urls))
                      progress_bar.progress(progress)


                      try:
                          # Process URL
                          clean_url = self.processor.clean_url(url)
                          cached_data = self.cache.get(clean_url)
                          if not cached_data:
                                  scraped_data = self.scraper.scrape_website(clean_url)
                                  self.cache.set(clean_url,scraped_data)
                          else:
                              scraped_data=cached_data

                          if debug_mode:
                              scrap_end_time=time()
                              debug_logs=debug_logs+f'\n {url} \n'
                              txt=f"webscrapping time : {scrap_end_time-url_start_time:.2f} seconds"
                              debug_logs=debug_logs+'\n'+txt
                              log_window.text(txt)

                          analysis = self.analyzer.analyze_with_ollama(scraped_data['content'], clean_url)

                          if debug_mode:
                              ollama_end_time=time()
                              txt=f"AI Based analysis time : {ollama_end_time-scrap_end_time:.2f} seconds"
                              debug_logs=debug_logs+'\n'+txt
                              log_window.text(txt)

                          result = {
                              'url': url,
                              'status': 'success',
                          }
                          # Extract location and product for advanced analytics
                          location        = analysis.get('location', '')
                          keywords        = analysis.get('keywords', '') 
                          target_audiences = analysis.get('target_audience', '') 
                          business_name = analysis.get('business_name', '') 
                          product_services = analysis.get('products_services', '') 

                          keyword_list = keywords.split(',')
                          result['business_name']=business_name
                          for i in range(5):
                            try:
                              result[f'keyword_{i+1}']=keyword_list[i]
                            except:
                              result[f'keyword_{i+1}']=''

                          product_services_list= product_services.split(',')
                          for i in range(3):
                            try:
                              result[f'product_services_{i+1}']=product_services_list[i]
                            except:
                              result[f'product_services_{i+1}']=''

                          target_audience_list= target_audiences.split(',')
                          for i in range(3):
                            try:
                              result[f'target_audiance_{i+1}']=target_audience_list[i]
                            except:
                              result[f'target_audiance_{i+1}']=''    

                          if features.get("top_competitor"):
                              try:
                                  top_competitors_list = self.analytics.find_top_competitors(keyword_list[0], location, clean_url, pages=3)
                                  for i in range(3):
                                      try:
                                        result[f'top_competitors_{i+1}']=top_competitors_list[i]
                                      except:
                                        result[f'target_audiance_{i+1}']=''  
                              except Exception as e:
                                  for i in range(3):
                                    result[f'top_competitors_{i+1}'] = ''
                                  result['status'] = 'Partial Error'
                                  result['error'] = f'Top Competitor error {e}'
                                  
                              if debug_mode:
                                  tc_end_time=time()
                                  txt=f"Top Competitor search time : {tc_end_time-ollama_end_time:.2f} seconds"
                                  debug_logs=debug_logs+'\n'+txt
                                  log_window.text(txt)
                          else:
                              tc_end_time=time()
                   
                          if features.get("gmb"):
                              try:
                                  gmb_setup = self.analytics.check_gmb_setup(clean_url)
                                  result["gmb_setup"] = gmb_setup
                              except Exception as e:
                                  result["gmb_setup"] = ''
                                  result['status'] = 'Partial Error'
                                  result['error'] = f'GMB error {e}'

                              if debug_mode:
                                  gmb_end_time=time()
                                  txt=f"GMB finding time : {gmb_end_time-tc_end_time:.2f} seconds"
                                  debug_logs=debug_logs+'\n'+txt
                                  log_window.text(txt)
                          else:
                              gmb_end_time=time()

                          if features.get("non_index_pages"):
                              try:
                                  indexed_pages = self.analytics.count_non_indexed_pages(clean_url)
                                  total_pages = self.analytics.count_total_pages(clean_url)
                                  non_index_pages = max(0, total_pages - indexed_pages)
                                  result["non_indexed_pages"] = non_index_pages
                              except Exception as e:
                                  result["non_indexed_pages"] = ''
                                  result['status'] = 'Partial Error'
                                  result['error'] = f'Non Index page find error {e}'

                              if debug_mode:
                                  ni_end_time=time()
                                  txt=f"Non Index Pages finding time: {ni_end_time-gmb_end_time:.2f} seconds"
                                  debug_logs=debug_logs+'\n'+txt
                                  log_window.text(txt)

                          results.append(result)
                          # batch_results.append(result)

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
                          # batch_results.append({
                          #     'url': url,
                          #     'status': 'error',
                          #     'error': str(e),
                          #     'top_competitors': '',
                          #     'gmb_setup': '',
                          #     'business_name': '',
                          #     'non_indexed_pages': ''
                          # })

                  # Save intermediate results after each batch
                  df = pd.DataFrame(results)
                  df = df.fillna(' ')
                  # df_batch = pd.DataFrame(batch_results)
                  st.session_state.results = df
                  
                  # Display results so far
                  self.components.display_results(df)

              # Save final results to a CSV file
              output_file = f"output/analysis/results_{timestamp}.csv"
              df.to_csv(output_file, index=False)

              if debug_mode:
                  end_time=time()
                  debug_logs=debug_logs+f"\n processing Completed \n Total {len(df)} urls with {len(df[df['status'] == 'success'])} successful urls, processed in {end_time-start_time:.2f} seconds"
                  debug_path=f'output/debug_logs/log_{timestamp}.txt'
                  with open(file=debug_path,mode='w') as f:
                      f.write(debug_logs)

                    # Reset processing state
              st.session_state.processing = False
              st.download_button(
                label="Download Complete Result", 
                data=open(output_file, 'rb').read(), 
                file_name="results.csv", 
                mime="text/csv"
                )
              st.session_state.processing = False
              st.success("Processing complete! Results saved.")

          except Exception as e:
              st.error(f"Error: {str(e)}")
              st.session_state.processing = False



if __name__ == "__main__":
    app = WebApp()
    app.run()
