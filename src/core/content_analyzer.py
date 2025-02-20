# src/analyzer/content_analyzer.py
import json
import requests
from typing import Dict, List
import re
import os
from datetime import datetime
from config.settings import OLLAMA_CONFIG
from config.prompts import ANALYSIS_PROMPT
import logging

# Configure logging for this module
logging.basicConfig(
    level=logging.DEBUG,  # Change level if needed
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ContentAnalyzer:
    def __init__(self, model=None, base_url=None):
        self.base_url = base_url or OLLAMA_CONFIG['BASE_URL']
        self.model = model or OLLAMA_CONFIG['MODEL']
        logging.debug("Initialized ContentAnalyzer with base_url: %s, model: %s", self.base_url, self.model)
    
    def _extract_contact_info(self, content: str) -> Dict:
        """Extract email and phone numbers using regex"""
        logging.debug("Extracting contact info from content (length: %d)", len(content))
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = list(set(re.findall(email_pattern, content)))
        
        # Phone pattern (various formats)
        phone_pattern = r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
        phones = list(set(re.findall(phone_pattern, content)))
        
        logging.debug("Extracted emails: %s, phones: %s", emails, phones)
        return {
            'emails': emails,
            'phones': phones
        }

    def analyze_with_ollama(self, content: str, url: str, model=None) -> dict:
        try:
            logging.debug("Starting Ollama analysis for URL: %s", url)
            formatted_prompt = ANALYSIS_PROMPT.format(
                url=url,
                content=content[:4000]
            )
            logging.debug("Formatted prompt: %s", formatted_prompt)
            model_to_infer = model or self.model
            timeout = 300 if model_to_infer in ["deepseek-r1:32b", "llama3.3:70b"] else 120

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_to_infer,
                    "prompt": formatted_prompt,
                    "temperature": OLLAMA_CONFIG['TEMPERATURE'],
                    "format": "json"
                },
                timeout=timeout
            )
            logging.debug("Ollama response status code: %s", response.status_code)
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        full_response += data['response']
            logging.debug("Full response from Ollama: %s", full_response)
            
            json_start = full_response.find('{')
            json_end = full_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis = json.loads(full_response[json_start:json_end])
                logging.debug("Parsed analysis JSON: %s", analysis)
            else:
                raise ValueError("No valid JSON found in response")

            # Validate required keys; if missing, assign defaults
            required_fields = ['keywords', 'business_name', 'products_services', 'target_audience', 'location']
            for field in required_fields:
                if field not in analysis:
                    logging.warning("Field '%s' not found in analysis. Setting default empty value.", field)
                    analysis[field] = ""

            return analysis

        except Exception as e:
            logging.error("Error in Ollama analysis for URL %s: %s", url, str(e))
            # Fallback: Return a default JSON so processing can continue
            return {
                "keywords": "",
                "business_name": "",
                "products_services": "",
                "target_audience": "",
                "location": "United States",
                "error": f"Fallback triggered: {str(e)}"
            }

    def process_scraped_data(self, input_json: str, output_file: str = None) -> Dict:
        """Process scraped data from JSON file"""
        try:
            logging.debug("Processing scraped data from file: %s", input_json)
            # Read scraped data
            with open(input_json, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)

            results = {}
            total = len(scraped_data)
            logging.info("Total URLs to process: %d", total)

            for i, (url, data) in enumerate(scraped_data.items(), 1):
                logging.info("Processing [%d/%d]: %s", i, total, url)
                try:
                    if data['status'] == 'success' and data.get('data'):
                        content = f"""
                        Title: {data['data'].get('title', '')}
                        Description: {data['data'].get('meta_description', '')}
                        Content: {data['data'].get('content', '')}
                        """
                        logging.debug("Combined content for URL %s", url)
                        
                        # Analyze with Ollama
                        analysis = self.analyze_with_ollama(content, url)
                        
                        results[url] = {
                            'status': 'success',
                            'analysis': analysis,
                            'timestamp': datetime.now().isoformat()
                        }
                        logging.info("Analysis successful for URL: %s", url)
                    else:
                        results[url] = {
                            'status': 'skipped',
                            'error': 'No valid content to analyze',
                            'timestamp': datetime.now().isoformat()
                        }
                        logging.warning("Skipped URL %s - No valid content", url)
                        
                except Exception as e:
                    results[url] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    logging.error("Error processing URL %s: %s", url, str(e))

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                logging.debug("Results saved to output file: %s", output_file)

            return results

        except Exception as e:
            logging.error("Error processing scraped data from file %s: %s", input_json, str(e))
            raise Exception(f"Error processing scraped data: {str(e)}")
