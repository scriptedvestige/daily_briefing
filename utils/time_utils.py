#!/usr/bin/env python3
import sys
sys.path.append('.')

from datetime import datetime, timedelta
from utils.file_utils import config_path
import json


# ISO Formats
def iso_format():
    """Return current date in full ISO 8601 format."""
    return datetime.today().strftime("%Y-%m-%d")
    
def iso_delta(count):
    """Return ISO 8601 date for count days in the future."""
    return (datetime.today() + timedelta(days=count)).strftime("%Y-%m-%d")

def filename_format():
    """Return current date in compact ISO 8601 format for file names."""
    return datetime.today().strftime("%Y%m%d")
    
def filename_delta(count):
    """Return the date delta in filename format."""
    return (datetime.today() + timedelta(days=count)).strftime("%Y%m%d")

# Filename Formats
def rss_format():
    """Return RSS feed date format."""
    return datetime.today().strftime("%d %b %Y")
    
def rss_yesterday():
    """Return yesterday's date in RSS format."""
    return (datetime.today() - timedelta(days=1)).strftime("%d %b %Y")

# Day Names    
def day_name():
    """Return name of current day."""
    return datetime.today().strftime("%A")
 
def day_name_delta(count):
    """Return name of day delta past/future."""
    return (datetime.today() + timedelta(days=count)).strftime("%A")

def future_dayname(date):
    """Return the day name for a date in the future.  yyyy-mm-dd -> name"""
    return datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    
def day_name_short():
    """Return shortened name of current day."""
    return datetime.today().strftime("%a")

# Briefing Format
def briefing_message_date():
    """Return the date formatted for the daily briefing."""
    return datetime.today().strftime("%a, %b %d")

# Full Date and Time
def current_date_time():
    """Return current date and time in format yyyy-mm-dd hh:mm:ss"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def current_time():
    """Return the current time."""
    return datetime.today().strftime("%H:%M:%S")

def time_of_day():
    """Determine morning versus midday based on hour."""
    if int(datetime.today().strftime("%H")) < 12:
        return "morning"
    else:
        return "midday"
    
def isPTO(date):
    """Determine if the date a paid day off."""
    pto = config_path("pto")
    with open(pto, "r") as file:
        data = json.load(file)
    if date in data["days_off"]:
        return True
    else:
        return False
    