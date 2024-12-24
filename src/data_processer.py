# src/data_processer.py
import pandas as pd
from urllib.parse import urlparse, urljoin
import re
from typing import List, Dict

class DataProcessor:
    def __init__(self):
        pass
    
    def read_excel_to_url(self, file_path: str) -> list:
        """Read Excel file"""
        try:
            df = pd.read_excel(file_path, header=None)
            df.columns = ['url']
            return df['url'].tolist()
            
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
        
    def clean_url(self, url: str) -> str:
        """Clean and validate URL, adding scheme if missing"""
        try:
            # Remove any leading/trailing whitespace
            url = url.strip()
            
            # Extract URLs if multiple are combined
            urls = re.findall(r'[\w\-\.]+\.[\w\-\.]+\w+', url)
            if urls:
                url = urls[0]  # Take the first URL if multiple are found
            
            # Parse the URL
            parsed = urlparse(url)
            
            # If no scheme is provided, add 'https://'
            if not parsed.scheme:
                url = 'https://' + url
                
            return url
            
        except Exception as e:
            raise Exception(f"Error processing URL {url}: {str(e)}")
    def store_result(self, url: str, scraped_data: Dict) -> str:
            """Store scraped data in JSON format"""
            try:
                # Create result object
                result = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success' if scraped_data['content'] else 'empty',
                    'data': {
                        'content': scraped_data['content'],
                        'metadata': {
                            'title': scraped_data['metadata'].get('title', ''),
                            'meta_description': scraped_data['metadata'].get('meta_description', ''),
                            'keywords': scraped_data['metadata'].get('keywords', []),
                            'headers': scraped_data['metadata'].get('headers', {}),
                        }
                    }
                }
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                domain = urlparse(url).netloc
                filename = f"{self.results_dir}/{domain}_{timestamp}.json"
                
                # Save to JSON file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                    
                return filename
                
            except Exception as e:
                raise Exception(f"Error storing results for {url}: {str(e)}")
