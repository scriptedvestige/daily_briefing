#!/usr/bin/env python3
# This is a hacky solution for manually testing individual modules.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from email.utils import parsedate_to_datetime
from utils.time_utils import filename_format, filename_delta, rss_format, rss_yesterday, time_of_day
from utils.file_utils import check_file, config_path, news_path
import feedparser
import json


class RssScraper():
    """Scrape RSS feeds from news sources listed in config."""
    def __init__(self):
        # Counters
        self.counter = 0
        self.morning_count = 0
        self.skipped_feeds = 0
        self.skipped_entries = 0
        # Time
        self.file_date = filename_format()
        self.yesterday_file = filename_delta(-1)
        self.today = rss_format()
        self.yesterday = rss_yesterday()
        self.time_of_day = time_of_day()
        # Variables
        self.config = config_path("news")
        self.topic = ""
        self.urls = []
        self.keywords = []
        self.all_titles = []
        self.articles = {"morning": {}, "midday": {}}
        self.articles_out = ""

    def load_config(self):
        """Assign config info to self variables."""
        with open(self.config, "r") as config:
            full_config = json.load(config)
        self.topic = full_config["topic"]
        self.urls = full_config["urls"]
        self.keywords = full_config["keywords"]
        
    def load_articles(self, date):
        """Load titles of articles in supplied json to list of all titles."""
        filepath = news_path(self.topic, date)
        if check_file(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
            # For index and values in dictionary...
            for index, entry in enumerate(data["morning"].values()):
                # Add title to list of all titles
                self.all_titles.append(entry["title"])
                # If file date is current date, add the morning entries to the articles list that will be saved later.
                if date == self.file_date:
                    self.articles["morning"][str(index)] = entry
            # Add midday articles to list of all articles if midday key contains data.
            if len(data["midday"].values()) > 0:
                for index, entry in enumerate(data["midday"].values()):
                    # Add title to list of all titles.
                    self.all_titles.append(entry["title"])
                    # If file date is current date, add any midday entries to the articles list that will be saved later.
                    if date == self.file_date:
                        self.articles["midday"][str(index)] = entry
            
    def scrape(self, time):
        """Run the scraper, return raw data."""
        for site in self.urls:
            try:
                data = feedparser.parse(site).entries
            except Exception:
                # If a single feed fails to fetch or parse, skip it — the rest still run.
                self.skipped_feeds += 1
                continue
            self.parse_data(time, data)

    def parse_published_date(self, raw):
        """Parse a feed's published/updated timestamp into a display date string, regardless of whether it's RFC 822 or ISO 8601."""
        if not raw:
            return None
        try:
            return parsedate_to_datetime(raw).strftime("%d %b %Y")
        except (TypeError, ValueError):
            pass
        try:
            return datetime.fromisoformat(raw).strftime("%d %b %Y")
        except ValueError:
            return None

    def parse_data(self, time, all_data):
        """Parse the data pulled by the scraper."""
        for entry in all_data:
            try:
                title = entry.get("title")
                link = entry.get("link")
                raw_published = entry.get("published") or entry.get("updated") or entry.get("pubDate")
                description = entry.get("description") or entry.get("summary") or ""
                if not title or not link or not raw_published:
                    # Skip entries missing the fields we actually need.
                    self.skipped_entries += 1
                    continue
                item = [title, raw_published, link, description]
                # If data is in relevant date range, contains keywords, and has not been sent in a briefing already.
                if self.check_date(item) and self.check_keywords(item) and self.check_repeat(item[0]):
                    self.add_article(time=time, index=str(self.counter), item=item)
                    self.counter += 1
            except Exception:
                # One malformed entry shouldn't take down the rest of the feed.
                self.skipped_entries += 1
                continue

    def check_date(self, item):
        """Check that published date matches yesterday or today."""
        pub_date = self.parse_published_date(item[1])
        if pub_date is None:
            return False
        return pub_date in (self.today, self.yesterday)
        
    def check_keywords(self, item):
        """Check title for relevent keywords."""
        title = item[0].lower()
        for word in self.keywords:
            if word.lower() in title:
                return True
        return False

    def check_repeat(self, title):
        """Return false if article was already sent in a briefing for the current day or day prior."""
        return title not in self.all_titles

    def add_article(self, time, index, item):
        """Add article to list if it passes all checks."""
        self.articles[time][index] = {"title": item[0], "published": item[1], "link":item[2], "description":item[3]}

    def save_file(self):
        """Save articles list to file."""
        filepath = news_path(self.topic, self.file_date)
        with open(filepath, "w") as file:
            json.dump(self.articles, file, indent=4)

    def format_data(self, time):
        """Format data for template injection in send email module."""
        if len(self.articles[time]) > 0:
            for item in self.articles[time].values():
                title = item["title"]
                link = item["link"]
                desc = item["description"]
                self.articles_out += f"<b>{title}</b><br>{desc}<br><a href='{link}' target='_blank'>{link}</a><br><br>"
        else:
            self.articles_out = "Take a moment to breathe!<br><br>"
        return self.articles_out

    def run(self):
        """Run all functions."""
        self.load_config()
        self.load_articles(self.yesterday_file)
        self.load_articles(self.file_date)
        self.scrape(self.time_of_day)
        self.save_file()
        print(f"[RSS] Feeds skipped: {self.skipped_feeds}/{len(self.urls)} | Entries skipped: {self.skipped_entries} | Articles matched: {self.counter}")
        return self.format_data(self.time_of_day)


if __name__ == "__main__":
    scraper = RssScraper()
    print(scraper.run())

