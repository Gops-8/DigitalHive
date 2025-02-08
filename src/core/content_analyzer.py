# src/analyzer/content_analyzer.py
import json
import requests
from typing import Dict, List
import re
import os
from datetime import datetime
from config.settings import OLLAMA_CONFIG
from config.prompts import ANALYSIS_PROMPT

class ContentAnalyzer:
    def __init__(self, model=None, base_url=None):
        self.base_url = base_url or OLLAMA_CONFIG['BASE_URL']
        self.model = model or OLLAMA_CONFIG['MODEL']
    
    def _extract_contact_info(self, content: str) -> Dict:
        """Extract email and phone numbers using regex"""
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = list(set(re.findall(email_pattern, content)))
        
        # Phone pattern (various formats)
        phone_pattern = r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
        phones = list(set(re.findall(phone_pattern, content)))
        
        return {
            'emails': emails,
            'phones': phones
        }

    def analyze_with_ollama(self, content: str, url: str, model=None) -> Dict:
        try:
            formatted_prompt = ANALYSIS_PROMPT.format(
                url=url,
                content=content[:4000]
            )
            model_to_infer = model or self.model
            # print(f"Prompt: {formatted_prompt}")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_to_infer,
                    "prompt": formatted_prompt,
                    "temperature": OLLAMA_CONFIG['TEMPERATURE'],
                    "format": "json"
                }
            )
            response.raise_for_status()
            
            # Parse Ollama response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        full_response += data['response']

            # Extract JSON from response
            json_start = full_response.find('{')
            json_end = full_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis = json.loads(full_response[json_start:json_end])
            else:
                raise ValueError("No valid JSON found in response")

            # Validate keys in analysis
            required_fields = ['keywords', 'headers']
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = []  # Default to empty list

            # # Extract contact information
            # contact_info = self._extract_contact_info(content)
            
            # # Combine all information
            # analysis.update(contact_info)
            
            return analysis

        except Exception as e:
            raise Exception(f"Error in Ollama analysis: {str(e)}")

    def process_scraped_data(self, input_json: str, output_file: str = None) -> Dict:
        """Process scraped data from JSON file"""
        try:
            # Read scraped data
            with open(input_json, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)

            results = {}
            total = len(scraped_data)

            for i, (url, data) in enumerate(scraped_data.items(), 1):
                print(f"\nProcessing [{i}/{total}]: {url}")
                
                try:
                    if data['status'] == 'success' and data.get('data'):
                        # Combine title, meta description and content for analysis
                        content = f"""
                        Title: {data['data'].get('title', '')}
                        Description: {data['data'].get('meta_description', '')}
                        Content: {data['data'].get('content', '')}
                        """
                        
                        # Analyze with Ollama
                        analysis = self.analyze_with_ollama(content, url)
                        
                        results[url] = {
                            'status': 'success',
                            'analysis': analysis,
                            'timestamp': datetime.now().isoformat()
                        }
                        print("✓ Analysis successful")
                    else:
                        results[url] = {
                            'status': 'skipped',
                            'error': 'No valid content to analyze',
                            'timestamp': datetime.now().isoformat()
                        }
                        print("✗ Skipped - No valid content")
                        
                except Exception as e:
                    results[url] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    print(f"✗ Error: {str(e)}")

            # Save results if output file specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

            return results

        except Exception as e:
            raise Exception(f"Error processing scraped data: {str(e)}")
