# crawler/config.py

class Config:
    """
    Configuration for the MusicMatcher crawler.
    This replaces the old assignment config and is tailored for
    Sweetwater + GuitarCenter guitar product crawling.
    """

    def __init__(self):
        # -----------------------
        # Seed URLs (starting points)
        # -----------------------
        self.seed_urls = [
            # Sweetwater electric guitars
            "https://www.sweetwater.com/c695--Electric_Guitars",

            # Guitar Center electric guitars
            "https://www.guitarcenter.com/Electric-Guitars.gc",
        ]

        # -----------------------
        # Crawler behavior
        # -----------------------
        self.threads_count = 4          # number of worker threads
        self.time_delay = 1.0           # fallback delay (robots.txt may override)
        self.max_pages = 5000           # safety limit to avoid runaway crawling

        # -----------------------
        # Networking
        # -----------------------
        self.user_agent = (
            "MusicMatcherBot/1.0 (+https://example.com/bot-info) "
            "Respectful crawler for academic research."
            "Will try my best to not be rude."
        )

        # Cache server (optional, from your old assignment)
        # If unused, set to None
        self.cache_server = None

        # -----------------------
        # Frontier persistence
        # -----------------------
        self.save_file = "frontier_state.db"

        # -----------------------
        # Output folder for scraped product JSON
        # -----------------------
        self.output_folder = "crawled_data"
