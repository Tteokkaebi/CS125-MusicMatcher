# crawler/frontier.py

import json
import threading
from pathlib import Path
from collections import deque


class Frontier:
    """
    Persistent, thread-safe URL frontier for MusicMatcher.
    Stores:
        - queue of URLs to crawl
        - visited set
        - persistent state on disk
    """

    def __init__(self, save_file="frontier_state.db"):
        self.save_file = Path(save_file)
        self.lock = threading.Lock()

        self.queue = deque()
        self.visited = set()

        # Load previous state if exists
        if self.save_file.exists():
            self._load_state()
        else:
            self._save_state()

    # -----------------------------
    # Persistence
    # -----------------------------
    def _save_state(self):
        data = {
            "queue": list(self.queue),
            "visited": list(self.visited)
        }
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _load_state(self):
        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.queue = deque(data.get("queue", []))
                self.visited = set(data.get("visited", []))
        except Exception:
            # If corrupted, reset
            self.queue = deque()
            self.visited = set()
            self._save_state()

    # -----------------------------
    # Frontier Operations
    # -----------------------------
    def add_url(self, url: str):
        with self.lock:
            if url not in self.visited and url not in self.queue:
                self.queue.append(url)
                self._save_state()

    def get_tbd_url(self):
        with self.lock:
            if not self.queue:
                return None
            url = self.queue.popleft()
            self.visited.add(url)
            self._save_state()
            return url

    def mark_url_complete(self, url: str):
        # Nothing to do except persist visited set
        with self.lock:
            self.visited.add(url)
            self._save_state()

    # -----------------------------
    # Utility
    # -----------------------------
    def is_empty(self):
        with self.lock:
            return len(self.queue) == 0
