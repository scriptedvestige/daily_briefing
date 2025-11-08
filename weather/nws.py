#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.time_utils import iso_format, filename_format
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
        self.header = "" # NWS requests a user-agent with contact info to use their API.

    def load_config(self):
        """Load parameters from the config file."""
        with open(self.config, "r+") as config:
            config_data = json.load(config)
            self.url = config_data["nws"]["url"]
            self.header = config_data["nws"]["user-agent"]

    def call_api(self):
        """Call API and write data to forecast.txt"""
        api_data = requests.get(url=self.url, headers=self.header).json()
        forecast = api_data["properties"]["periods"]
        return forecast

    def save_file(self, forecast):
        """Save forcast data to json file."""
        with open(self.json_dump, "w") as file:
            json.dump(forecast, file, indent=4)

    def build_message(self, forecast):
        """Build the daily message from the forecast data."""
        for number in range(0,3):
            line = forecast[number]
            day_name = line["name"]
            detailed_forecast = line["detailedForecast"]
            self.daily_message += f"<b><u>{day_name}</u></b><br>{detailed_forecast}<br><br>"
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
