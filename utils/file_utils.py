#!/usr/bin/env python3

import os

def root_dir():
    """Define the path of the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def build_path(dir, subdir):
    """Build a path from a directory to a subdirectory."""
    return os.path.join(dir, subdir)
    
def check_file(path):
    """Check if a file path exists."""
    return os.path.exists(path)
    
##### MODULE DIRECTORIES #####
def wardrobe_dir():
    """Wardrobe subdirectory path."""
    return os.path.join(root_dir(), "wardrobe")
    
def news_dir():
    """News subdirectory path."""
    return os.path.join(root_dir(), "news")
    
def weather_dir():
    """Weather subdirectory path."""
    return os.path.join(root_dir(), "weather")
    
def alerts_dir():
    """Alerts subdirectory path."""
    return os.path.join(root_dir(), "alerts")
    
##### CONFIGURATIONS #####
def configs_dir():
    """Configurations subdirectory path."""
    return os.path.join(root_dir(), "configs")
    
def config_path(mod_name):
    """Config filename path."""
    return os.path.join(configs_dir(), f"{mod_name}_config.json")
    
##### TEMPLATES #####
def templates_dir():
    """Templates subdirectory path."""
    return os.path.join(root_dir(), "templates")
    
def briefing_template(time_of_day):
    """Briefing template path.  Choose appropriate template based on time of day."""
    return os.path.join(templates_dir(), f"{time_of_day}_email.html")
    
def preview_template():
    """Weely wardrobe preview path."""
    return os.path.join(templates_dir(), "wardrobe_preview.html")
    
def wardrobe_template():
    """Wardrobe schedule template path."""
    return os.path.join(templates_dir(), "wardrobe_template.json")
    
##### OUTPUT #####
def weather_out():
    """Path for output from weather module."""
    return os.path.join(weather_dir(), "output")
    
def todays_forecast(date):
    """Daily weather output filename."""
    return os.path.join(weather_out(), f"nws_{date}.json")

def wardrobe_out():
    """Path for output from wardrobe module."""
    return os.path.join(wardrobe_dir(), "output")

def last_weekly_wardrobe(date):
    """Weekly wardrobe schedule filename.  For loading schedule on days schedule not generated."""
    return os.path.join(wardrobe_out(), f"weekly_plan_{date}.json")

def news_out():
    """Path for output from news module."""
    return os.path.join(news_dir(), "output")

def alerts_out():
    """Path for output from alerts module."""
    return os.path.join(alerts_dir(), "output")
    
def sent_brief_title(time_of_day, date):
    """Briefing output filename."""
    return os.path.join(alerts_out(), f"{time_of_day}_briefing_{date}.html")

def weekly_wardrobe(date):
    """Weekly wardrobe schedule filename."""
    return os.path.join(wardrobe_out(), f"weekly_plan_{date}.json")
    
def sent_preview_title(date):
    """Weekly wardrobe preview filename."""
    return os.path.join(alerts_out(), f"wardrobe_preview_{date}.html")
