import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

class AnalysisCache:
    def __init__(self, cache_dir="output/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _hash_url(self, url: str) -> str:
        """Create a unique hash for the URL."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _is_valid(self, timestamp: str, expiry_duration: int = 7) -> bool:
        """Check if the cache is still valid based on the timestamp."""
        cache_time = datetime.fromisoformat(timestamp)
        return datetime.now() - cache_time < timedelta(days=expiry_duration)

    def get(self, url: str) -> Optional[Dict]:
        """Retrieve cached analysis for a URL if valid."""
        cache_file = os.path.join(self.cache_dir, f"{self._hash_url(url)}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if self._is_valid(data['timestamp']):
                    return data['analysis']
        return None

    def set(self, url: str, analysis: Dict):
        """Save analysis data to cache."""
        cache_file = os.path.join(self.cache_dir, f"{self._hash_url(url)}.json")
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis
            }, f)
