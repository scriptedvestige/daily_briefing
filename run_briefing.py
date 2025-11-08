#!/usr/bin/env python3

from weather import nws
from wardrobe import generator
from news import news_scraper, cve
from alerts import send_email
from cleaner import CleanUp

# Data
forecast = ""
wardrobe = ""
cyber_news = ""
cves = ""

def beep_boop():
    """I am become cron, runner of modules."""
    # Run forecast module.
    fc = nws.WeatherForecast()
    forecast = fc.run()
    # Run wardrobe module.
    gen = generator.WardrobeGenerator()
    wardrobe = gen.run()
    # Run news module.
    cyber = news_scraper.NewsScaper()
    cyber_news = cyber.run()
    # Run CVE module.
    vulns = cve.CveScraper()
    cves = vulns.run()
    # Send all the data.
    email = send_email.Emailer(
        forecast=forecast, 
        wardrobe=wardrobe, 
        news=cyber_news, 
        cves=cves
        )
    email.run()
    # Clean up old files.
    janitor = CleanUp()
    janitor.run()

if __name__ == "__main__":
    beep_boop()
