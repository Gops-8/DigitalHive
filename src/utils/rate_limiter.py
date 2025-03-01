import time
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_minute=30, burst_limit=10):
        self.rate_limit = requests_per_minute
        self.burst_limit = burst_limit
        self.requests = deque()

    def wait(self):
        now = datetime.now()
        while self.requests and now - self.requests[0] > timedelta(minutes=1):
            self.requests.popleft()

        if len(self.requests) >= self.burst_limit:
            sleep_time = (self.requests[0] + timedelta(seconds=60 / self.burst_limit) - now).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.requests.append(now)
