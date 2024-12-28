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
        print(f"DEBUG: Username={username}, Password={password}")
        if username not in self.credentials:
            print(f"DEBUG: Invalid Username={username}")
            return False
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print(f"DEBUG: Hashed Password={hashed_password}, Expected={self.credentials[username]}")
        return hashed_password == self.credentials[username]

