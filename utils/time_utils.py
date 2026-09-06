#!/usr/bin/env python3
# This is a hacky solution for manually testing individual modules.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta
from utils.file_utils import config_path
import json


# ----- ISO DATE FORMATS ----- #
def iso_format():
    """Return current date in full ISO 8601 format (YYYY-MM-DD)."""
    return datetime.today().strftime("%Y-%m-%d")

def iso_delta(count):
    """Return ISO 8601 date for count days in the future (or past, if negative)."""
    return (datetime.today() + timedelta(days=count)).strftime("%Y-%m-%d")


# ----- FILENAME DATE FORMATS ----- #
def filename_format():
    """Return current date in compact format for file names (YYYYMMDD)."""
    return datetime.today().strftime("%Y%m%d")

def filename_delta(count):
    """Return the date delta in filename format."""
    return (datetime.today() + timedelta(days=count)).strftime("%Y%m%d")


# ----- RSS DATE FORMATS ----- #
def rss_format():
    """Return today's date in RSS feed format."""
    return datetime.today().strftime("%d %b %Y")

def rss_yesterday():
    """Return yesterday's date in RSS feed format."""
    return (datetime.today() - timedelta(days=1)).strftime("%d %b %Y")


# ----- DAY NAMES ----- #
def day_name():
    """Return name of the current day."""
    return datetime.today().strftime("%A")

def day_name_delta(count):
    """Return name of the day count days in the future (or past, if negative)."""
    return (datetime.today() + timedelta(days=count)).strftime("%A")

def future_dayname(date):
    """Return the day name for a future date string (YYYY-MM-DD)."""
    return datetime.strptime(date, "%Y-%m-%d").strftime("%A")

def day_name_short():
    """Return abbreviated name of the current day."""
    return datetime.today().strftime("%a")


# ----- BRIEFING FORMAT ----- #
def briefing_message_date():
    """Return the date formatted for the daily briefing."""
    return datetime.today().strftime("%a, %b %d")


# ----- FULL DATE AND TIME ----- #
def current_date_time():
    """Return current date and time (YYYY-MM-DD HH:MM:SS)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def current_time():
    """Return the current time (HH:MM:SS)."""
    return datetime.today().strftime("%H:%M:%S")

def time_of_day():
    """Determine morning versus midday based on the current hour."""
    if int(datetime.today().strftime("%H")) < 12:
        return "morning"
    return "midday"


# ----- PTO ----- #
def is_pto(date):
    """Determine if the given date (YYYY-MM-DD) is a paid day off."""
    pto = config_path("pto")
    with open(pto, "r") as file:
        data = json.load(file)
    return date in data["days_off"]


if __name__ == "__main__":
    print(day_name())
