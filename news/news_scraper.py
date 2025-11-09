#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.time_utils import filename_format, filename_delta, rss_format, rss_yesterday, time_of_day
from utils.file_utils import check_file, config_path, news_out
import feedparser
import json
import os


class NewsScaper():
    """Scrape RSS feeds from news sources listed in config."""
    def __init__(self):
        # Counters
        self.counter = 0
        self.morning_count = 0
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
        with open(self.config, "r+") as config:
            full_config = json.load(config)
            self.topic += full_config["topic"]
            self.urls += full_config["urls"]
            self.keywords += full_config["keywords"]
        
    def load_articles(self, date):
        """Load titles of articles in supplied json to list of all titles."""
        filename = f"{self.topic}_news_{date}.json"
        filepath = os.path.join(news_out(), filename)
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
            data = feedparser.parse(site)
            self.parse_data(time, data)

    def parse_data(self, time, all_data):
        """Parse the data pulled by the scraper."""
        for i in range(len(all_data["entries"])):
            item = all_data["entries"][i]
            parsed = self.get_item(item)
            # If data is in relevent date range, contains keywords, and has not been sent in a briefing already.
            if self.check_date(parsed) and self.check_keywords(parsed) and self.check_repeat(parsed[0]):
                self.add_article(time=time, index=str(self.counter), item=parsed)
                self.counter += 1

    def get_item(self, data):
        """Get the title, published date, link, and description for an item in the raw data."""
        item = [data["title"], data["published"][5:16], data["link"], data["description"]]
        return item

    def check_date(self, item):
        """Check that published date matches yesterday or today."""
        if self.yesterday == item[1] or self.today == item[1]:
            return True
        else:
            return False
        
    def check_keywords(self, item):
        """Check title for relevent keywords."""
        for word in self.keywords:
            if word.lower() in item[0].lower():
                return True
            else:
                continue

    def check_repeat(self, title):
        """Return false if article was already sent in a briefing for the current day or day prior."""
        if title not in self.all_titles:
            return True
        else:
            return False

    def add_article(self, time, index, item):
        """Add article to list if it passes all checks."""
        self.articles[time][index] = {"title": item[0], "published": item[1], "link":item[2], "description":item[3]}

    def save_file(self):
        """Save articles list to file."""
        filename = f"{self.topic}_news_{self.file_date}.json"
        filepath = os.path.join(news_out(), filename)
        with open (filepath, "w") as file:
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
            self.articles_out = "Take a moment to breathe!"
        return self.articles_out

    def run(self):
        """Run all functions."""
        self.load_config()
        self.load_articles(self.yesterday_file)
        self.load_articles(self.file_date)
        self.scrape(self.time_of_day)
        self.save_file()
        return self.format_data(self.time_of_day)


if __name__ == "__main__":
    scraper = NewsScaper()
    scraper.run()
