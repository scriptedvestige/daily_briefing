#!/usr/bin/env python3

from pathlib import Path


def root_dir():
    """Define the path of the project root directory."""
    return Path(__file__).resolve().parent.parent

def check_file(path):
    """Check if a file path exists."""
    return Path(path).exists()

def build_path(dir, subdir):
    """Build a path from a directory to a subdirectory."""
    return Path(dir) / subdir

def cve_check_path(date):
    """CVE check output filename."""
    return news_out() / f"cve_check_{date}.json"

##### MODULE DIRECTORIES #####
def wardrobe_dir():
    """Wardrobe subdirectory path."""
    return root_dir() / "wardrobe"

def news_dir():
    """News subdirectory path."""
    return root_dir() / "news"

def news_path(topic, date):
    """News scraper output filename for a given topic and date."""
    return news_out() / f"{topic}_news_{date}.json"

def weather_dir():
    """Weather subdirectory path."""
    return root_dir() / "weather"

def alerts_dir():
    """Alerts subdirectory path."""
    return root_dir() / "alerts"

##### CONFIGURATIONS #####
def configs_dir():
    """Configurations subdirectory path."""
    return root_dir() / "configs"

def config_path(mod_name):
    """Config filename path."""
    return configs_dir() / f"{mod_name}_config.json"

##### TEMPLATES #####
def templates_dir():
    """Templates subdirectory path."""
    return root_dir() / "templates"

def briefing_template(time_of_day):
    """Briefing template path.  Choose appropriate template based on time of day."""
    return templates_dir() / f"{time_of_day}_email.html"

def preview_template():
    """Weekly wardrobe preview path."""
    return templates_dir() / "wardrobe_preview.html"

def wardrobe_template():
    """Wardrobe schedule template path."""
    return templates_dir() / "wardrobe_template.json"

##### KEY STORAGE #####
def key_dir():
    """Directory for the encryption key, kept outside the project repo."""
    return Path.home() / ".config" / "briefing"

def key_path():
    """Path to the Fernet encryption key."""
    return key_dir() / "config_key.key"

##### OUTPUT #####
def weather_out():
    """Path for output from weather module."""
    return weather_dir() / "output"

def todays_forecast(date):
    """Daily weather output filename."""
    return weather_out() / f"nws_{date}.json"

def wardrobe_out():
    """Path for output from wardrobe module."""
    return wardrobe_dir() / "output"

def last_weekly_wardrobe(date):
    """Weekly wardrobe schedule filename.  For loading schedule on days schedule not generated."""
    return wardrobe_out() / f"weekly_plan_{date}.json"

def news_out():
    """Path for output from news module."""
    return news_dir() / "output"

def alerts_out():
    """Path for output from alerts module."""
    return alerts_dir() / "output"

def sent_brief_title(time_of_day, date):
    """Briefing output filename."""
    return alerts_out() / f"{time_of_day}_briefing_{date}.html"

def weekly_wardrobe(date):
    """Weekly wardrobe schedule filename."""
    return wardrobe_out() / f"weekly_plan_{date}.json"

def sent_preview_title(date):
    """Weekly wardrobe preview filename."""
    return alerts_out() / f"wardrobe_preview_{date}.html"

