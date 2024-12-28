# src/utils/cache.py
import json
import os
from datetime import datetime, timedelta

class AnalysisCache:
    def __init__(self, cache_dir="output/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get(self, url: str) -> Dict:
        cache_file = os.path.join(self.cache_dir, f"{self._hash_url(url)}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if self._is_valid(data['timestamp']):
                    return data['analysis']
        return None

    def set(self, url: str, analysis: Dict):
        cache_file = os.path.join(self.cache_dir, f"{self._hash_url(url)}.json")
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis
            }, f)
