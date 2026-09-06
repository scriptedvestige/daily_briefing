#!/usr/bin/env python3
# This is a hacky solution for manually testing individual modules.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.time_utils import iso_format, filename_format, day_name, is_pto
from utils.file_utils import config_path, todays_forecast
import requests
import json


class WeatherForecast:
    """These functions will pull weather forecast information from NWS."""
    def __init__(self):
        # Date
        self.today = iso_format()
        # File paths
        self.config = config_path("weather")
        self.json_dump = todays_forecast(filename_format())
        # Message
        self.daily_message = ""
        # API
        self.url = ""
        self.header = {}

    def select_endpoint(self):
        """Choose 'work' or 'home' NWS config based on day type."""
        if day_name() in ("Saturday", "Sunday") or is_pto(self.today):
            return "home"
        return "work"

    def load_config(self):
        """Load parameters from the config file."""
        with open(self.config, "r") as config:
            config_data = json.load(config)
        endpoint = self.select_endpoint()
        self.url = config_data["nws"][endpoint]["url"]
        self.header = config_data["nws"][endpoint]["user-agent"]

    def call_api(self):
        """Call API and return forecast periods."""
        response = requests.get(url=self.url, headers=self.header, timeout=10)
        response.raise_for_status()
        api_data = response.json()
        forecast = api_data["properties"]["periods"]
        return forecast

    def save_file(self, forecast):
        """Save forecast data to json file."""
        with open(self.json_dump, "w") as file:
            json.dump(forecast, file, indent=4)

    def build_message(self, forecast):
        """Build the daily message from the forecast data."""
        periods = min(3, len(forecast))
        for number in range(periods):
            line = forecast[number]
            period_name = line["name"]
            detailed_forecast = line["detailedForecast"]
            self.daily_message += f"<b><u>{period_name}</u></b><br>{detailed_forecast}<br><br>"
        return self.daily_message
    
    def run(self):
        """Run all the functions to get the forecast data and return the daily message."""
        self.load_config()
        forecast_data = self.call_api()
        self.save_file(forecast_data)
        self.build_message(forecast_data)
        return self.daily_message


if __name__ == "__main__":
    data = WeatherForecast()
    message = data.run()
    print(message)
