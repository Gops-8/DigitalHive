# src/utils/auth.py
import requests
import hashlib
from config.settings import AUTH_CONFIG_URL

class AuthManager:
    def __init__(self):
        self.credentials = self._fetch_credentials()

    def _fetch_credentials(self):
        try:
            response = requests.get(AUTH_CONFIG_URL)
            return response.json()
        except:
            # Fallback to local credentials if remote fetch fails
            return {"admin": "password123"}

    def verify_credentials(self, username: str, password: str) -> bool:
        if username not in self.credentials:
            return False
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        stored_hashed_password = hashlib.sha256(self.credentials[username].encode()).hexdigest()
        return hashed_password == stored_hashed_password

