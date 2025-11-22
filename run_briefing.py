#!/usr/bin/env python3
import traceback
from datetime import datetime
from functools import wraps

from utils.file_utils import root_dir, build_path
from weather import nws
from wardrobe import generator
from news import rss, cve
from alerts import send_email
from cleaner import CleanUp

LOG_PATH = build_path(root_dir(), "cron.log")

# ----- DECORATOR ----- #
def safe_run(module_name):
    """Decorator that runs a function safely and logs any exceptions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                with open(LOG_PATH, "a") as log:
                    log.write(f"\n[{datetime.now()}] Error in {module_name}:\n")
                    log.write(f"{e}\n")
                    log.write(traceback.format_exc())
                    log.write("\n" + "-"*60 + "\n")
                    return f"{module_name} failed - check cron.log<br><br>"
        return wrapper
    return decorator

# ----- MODULE RUNNERS ----- #
@safe_run("Weather Forecast")
def run_forecast():
    fc = nws.WeatherForecast()
    return fc.run()

@safe_run("Wardrobe Generator")
def run_wardrobe():
    gen = generator.WardrobeGenerator()
    return gen.run()

@safe_run("News Scraper")
def run_news():
    cyber = rss.RssScraper()
    return cyber.run()

@safe_run("CVE Scraper")
def run_cves():
    vulns = cve.CveScraper()
    return vulns.run()

@safe_run("Emailer")
def run_email(forecast, wardrobe, cyber_news, cves):
    email = send_email.Emailer(
        forecast=forecast, 
        wardrobe=wardrobe, 
        news=cyber_news, 
        cves=cves
        )
    return email.run()

@safe_run("Janitor")
def run_cleaner():
    janitor = CleanUp()
    return janitor.run()

# ----- MAIN ORCHESTRATION ----- # 
def beep_boop():
    """I am become cron, runner of modules."""
    # Gather data for email.
    forecast = run_forecast()
    wardrobe = run_wardrobe()
    cyber_news = run_news()
    cves = run_cves()
    # Send email.
    run_email(forecast, wardrobe, cyber_news, cves)
    # Clean up old files.
    run_cleaner()

if __name__ == "__main__":
    beep_boop()
