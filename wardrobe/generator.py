#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.time_utils import day_name, time_of_day, filename_format, filename_delta, future_dayname, current_date_time, isPTO, iso_format
from utils.file_utils import wardrobe_template, weekly_wardrobe, last_weekly_wardrobe, todays_forecast, check_file, config_path
import json
import random


class WardrobeGenerator():
    """
    Generate the wardrobe schedule for the work week based on the weather forecast on Sundays.  
    On workdays, load the schedule, double check the items are still appropriate for the weather, format data for injection into template.
    Now I can blame my fashion fails on a computer!
    """
    def __init__(self):
        # Dates
        self.workdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.today = day_name()
        self.curr_date = iso_format()
        # Schedule
        self.schedule_template = wardrobe_template()
        self.save_schedule_path = weekly_wardrobe(filename_format())
        self.last_sunday_path = last_weekly_wardrobe(self.sunday_date())
        self.schedule = {}
        # Config
        self.config_path = config_path("wardrobe")
        self.temp_rules = {}
        self.precip_rules = {}
        self.inventory = {}
        self.priority = {}
        # Forecast
        self.forecast_path = todays_forecast(filename_format())
        self.weekly_fc = {}
        self.parsed_fc = {}

    def sunday_date(self):
        """Determine the date for the most recent Sunday."""
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if self.today != "Sunday":
            return filename_delta(-(all_days.index(self.today) + 1))
        else:
            return filename_format()

    def load_config(self):
        """Load the inventory json."""
        with open(self.config_path, "r") as file:
            self.inventory = json.load(file)
        self.temp_rules = self.inventory["rules"]["temp"]
        self.precip_rules = self.inventory["rules"]["precip"]

    def load_forecast(self):
        """Load the forecast json."""
        if check_file(self.forecast_path):
            with open(self.forecast_path, "r") as forecast:
                self.weekly_fc = json.load(forecast)
            return True
        else:
            return False

    def parse_forecast(self):
        """Parse the forecast json."""
        for dict in self.weekly_fc:
            date = dict["startTime"].split("T")[0]
            dayname = future_dayname(date)
            if dict["isDaytime"] and dayname in self.workdays:
                dayname = dayname
                temp = dict["temperature"]
                precip = dict["probabilityOfPrecipitation"]["value"]
                wind = int(dict["windSpeed"].split()[-2])
                feels_like = self.feels_like_temp(raw_temp=temp, wind_speed=wind)
                self.parsed_fc[dayname] = {"date":date, "temp":temp, "feelsLike":feels_like, "precip":precip, "wind":wind}

    def get_template(self):
        """Load the template to build the schedule."""
        with open(self.schedule_template, "r") as template:
            self.schedule = json.load(template)

    def check_temp_range(self, temp, shirts):
        """Check the temp value from the forecast against the ranges for shirts."""
        for i, (low, high) in enumerate(self.temp_rules["range"]):
            if low <= temp <= high:
                choice = shirts[i]
                return choice

    def check_precip_range(self, precip, boots):
        """Check the precip value from the forecast against the ranges for boots."""
        for i, (low, high) in enumerate(self.precip_rules["range"]):
            if low <= precip <= high:
                return boots[i]

    def feels_like_temp(self, raw_temp, wind_speed):
        """Adjust raw temp based on wind speed."""
        if raw_temp <= 50 and wind_speed >= 3:
            # Use NOAA wind chill formula.  This formula is only for raw temperatures below 50*F.
            v = wind_speed
            t = raw_temp
            feels_like = (
                36.74 + 0.6215 * t - 35.75 * (v ** 0.16) + 0.4275 * t * (v ** 0.16)
            )
            return round(feels_like, 1)
        elif 50 < raw_temp <= 65:
            # If raw temp between 50 and 65, make slight adjustment.
            return round(raw_temp - (wind_speed * 0.1))
        else:
            return raw_temp
        
    def temp_score(self, shirt_type, feels_like):
        """Determine the score of the feels like temperature."""
        weight = 3.0
        index = self.temp_rules["shirt"].index(shirt_type)
        return abs(feels_like - self.temp_rules["range"][index][1]) * weight
    
    def precip_score(self, precip):
        """Determine the score of the precipitation chance.  Curved scale, higher rain chance equals bigger penalty."""
        weight = 0.5
        return ((precip / 100) ** 1.5) * 100 * weight
        
    def day_score(self, temp_score, precip_score):
        """Score days based on how close to ideal they are given their shirt type range."""
        return temp_score + precip_score

    def prioritize_days(self):
        """Set the priority of the day based on it's score."""
        for day in self.parsed_fc:
            # Choose shirt type based on forecasted temperature.
            shirt_type = self.check_temp_range(temp=self.parsed_fc[day]["feelsLike"], shirts=self.temp_rules["shirt"])
            # Score the day for it's priority and add to dictionary.
            self.priority[day] = [self.day_score(temp_score=self.temp_score(
                shirt_type=shirt_type, feels_like=self.parsed_fc[day]["feelsLike"]), 
                precip_score=self.precip_score(self.parsed_fc[day]["precip"])
                ),
                shirt_type]
        # Sort the priority dictionary.
        self.priority = dict(sorted(self.priority.items(), key=lambda item: item[1]))

    def build_days(self):
        """Choose the items for the given day."""
        for day in self.priority:
            if not isPTO(self.parsed_fc[day]["date"]):
                boot_type = self.check_precip_range(precip=self.parsed_fc[day]["precip"], boots=self.precip_rules["boots"])
                boot_color = self.choose_boots(boot_type).split()[0]
                chino_inv = self.inventory["rules"]["boots"][boot_color]
                shirt = self.choose_chinos(boots=boot_color, chinos=chino_inv, shirt=self.priority[day][1], day=day)
                shirt_choice = self.choose_shirt(shirt, day)
                self.remove_shirt(shirt_type=shirt, shirt_choice=shirt_choice)
            else:
                self.schedule[day] = "No work today!"

    def choose_boots(self, boots):
        """Choose boots for a given day."""
        if boots == "captain":
            boots = random.choice(self.inventory["captain"])
        return boots

    def choose_chinos(self, boots, chinos, shirt, day):
        """Choose the color chinos and return shirt type."""
        adj_options = chinos
        shirt_type = ""
        # If no button downs left, choose flannel instead.
        if shirt == "button_down" and len(self.inventory[shirt]) == 0:
            shirt_type = "flannel"
        else:
            shirt_type = shirt
        # If shirt is button down, exclude navy, congos, and greenwoods chinos.
        if shirt_type == "button_down":
            adj_options = self.adjust_options(boots)
        chinos = random.choice(adj_options)
        self.remove_chinos(chinos)
        # Save boot color and chinos to schedule for the given day
        self.schedule[day]["boots"] = boots
        self.schedule[day]["chinos"] = chinos
        self.choose_belt(boots, day)
        if isinstance(shirt_type, list):
            return shirt_type[0]
        else:
            return shirt_type
    
    def adjust_options(self, boot):
        """Use adjusted inventory to account for button down rules."""
        adjusted_options = self.inventory["rules"]["boots"][boot].copy()
        if "navy" in adjusted_options:
            adjusted_options.remove("navy")
        if "congos" in adjusted_options:
            adjusted_options.remove("congos")
        if "greenwoods" in adjusted_options:
            adjusted_options.remove("greenwoods")
        return adjusted_options

    def remove_chinos(self, chinos):
        """Remove the selected chinos from all lists in inventory."""
        self.inventory["chinos"].remove(chinos)
        for key in self.inventory["rules"]["boots"].keys():
            if chinos in self.inventory["rules"]["boots"][key]:
                self.inventory["rules"]["boots"][key].remove(chinos)

    def choose_belt(self, boots, day):
        """Choose the appropriate belt for the day."""
        if boots == "canyon" or boots == "danner":
            self.schedule[day]["belt"] = "canyon"
        else:
            self.schedule[day]["belt"] = "black"

    def choose_shirt(self, shirt_type, day):
        """Choose a shirt color based on chino color."""
        shirt = ""
        if type(shirt_type) == list:
            shirt = shirt_type[1]
            self.schedule[day]["jacket"] = "Yes"
        elif self.parsed_fc[day]["precip"] >= 31:
            self.schedule[day]["jacket"] = "Yes"
        else:
            self.schedule[day]["jacket"] = "No"
        if shirt_type == "button_down" and len(self.inventory[shirt_type]) == 0:
            shirt == "flannel"
        else:
            shirt = shirt_type
        chino_color = self.schedule[day]["chinos"]
        # Grab acceptable shirt colors for chino color
        chino_rules = self.inventory["rules"]["chinos"][chino_color]
        # Make list of available shirts to choose from based on type and color picked.
        # Navy/black and olive/black button downs acceptable with black chinos.  Otherwise, black shirt not allowed with black chinos.
        if shirt == "button_down" and chino_color == "black":
            adjusted_rules = chino_rules.copy()
            adjusted_rules.append("black")
        else:
            adjusted_rules = chino_rules.copy()
        # Make a list of shirt options based on shirt type and acceptable colors per pant color.
        shirt_options = [x for x in self.inventory[shirt] if all(part in adjusted_rules for part in x.split("/"))]
        if len(shirt_options) > 0:
            shirt_choice = random.choice(shirt_options)
        else:
            shirt_choice = self.retry_choices(chino_color, shirt, day)
        self.schedule[day]["shirt"] = f"{shirt_choice} {shirt}"
        return shirt_choice

    def remove_shirt(self, shirt_type, shirt_choice):
        """Remove chosen shirt from inventory."""
        self.inventory[shirt_type].remove(shirt_choice)

    def retry_choices(self, chino, shirt, day):
        """If no options available for item, choose new item."""
        boot_color = self.schedule[day]["boots"]
        adj_options = self.inventory["rules"]["boots"][boot_color].copy()
        self.choose_chinos(boots=boot_color, chinos=adj_options, shirt=shirt, day=day)
        new_shirt = self.choose_shirt(shirt_type=shirt, day=day)
        self.inventory["rules"]["boots"][boot_color].append(chino)
        return new_shirt

    def save_schedule(self):
        """Save the generated weekly schedule."""
        if self.today == "Sunday":
            with open(self.save_schedule_path, "w") as sched:
                json.dump(self.schedule, sched, indent=4)
        else:
            with open(self.last_sunday_path, "w") as sched:
                json.dump(self.schedule, sched, indent=4)

    def load_schedule(self):
        """Load the weekly schedule."""
        # If weekly schedule file exists, load it.
        if check_file(self.last_sunday_path):
            with open(self.last_sunday_path, "r") as sched:
                self.schedule = json.load(sched)
            return True
        else:
            self.schedule = "Weekly schedule does not exist."
            return False

    def double_check_boots(self):
        """Check updated forecast data and verify boots are still appropriate."""
        new_precip = self.parsed_fc[self.today]["precip"]
        new_temp = self.parsed_fc[self.today]["feelsLike"]
        # Get boot based on new precipitation chance.
        boot_type = self.check_precip_range(precip=new_precip, boots=self.precip_rules["boots"])
        # Get shirt based on new temp.
        shirt_type = self.check_temp_range(temp=new_temp, shirts=self.temp_rules["shirt"])
        # If new boot different than scheduled boot, choose different boots, chinos, and belt for current day.
        if self.schedule[self.today]["boots"].split()[-1] != boot_type:
            boot_color = self.choose_boots(boot_type)
            self.schedule[self.today]["boots"] = boot_color
            chinos = self.inventory["rules"]["boots"][boot_color.split()[0]]
            if self.schedule[self.today]["chinos"] not in chinos:
                self.choose_chinos(boots=boot_color, chinos=chinos, shirt=shirt_type, day=self.today)
            self.choose_belt(boots=boot_color, day=self.today)

    def double_check_shirt(self):
        """Check updated forecast data and verify shirt is still appropriate."""
        shirt = ""
        new_temp = self.parsed_fc[self.today]["feelsLike"]
        # Get shirt type based on new temperature.
        shirt_type = self.check_temp_range(temp=new_temp, shirts=self.temp_rules["shirt"])
        # Check to ensure inventory greater than 0 for shirt type.
        if len(self.inventory[shirt_type]) == 0:
            pass
        # If shirt type is list ["jacket", "flannel"], select flannel.
        if type(shirt_type) == list:
            shirt = shirt_type[1]
        else:
            shirt = shirt_type
        # If new shirt is different than scheduled shirt, choose a different shirt.
        if shirt not in self.schedule[self.today]["shirt"] and len(self.inventory[shirt]) > 0:
            shirt_choice = self.choose_shirt(shirt_type=shirt, day=self.today)
            self.remove_shirt(shirt_type=shirt_type, shirt_choice=shirt_choice)

    def update_inventory(self):
        """Update the inventory for the selected item for schedule rebuilds."""
        used_inventory = {}
        # Create a list of all items used in schedule.
        for key, value in self.schedule.items():
            if self.today != key and key != "Saturday" and key != "Sunday" and value is dict:
                used_inventory[key] = value
        # Remove items used on other days from current inventory.
        for value in used_inventory.values():
            self.remove_chinos(chinos=value["chinos"])
            shirt_color = value["shirt"].split()[0]
            shirt_type = value["shirt"].split()[1]
            if shirt_color in self.inventory[shirt_type]:
                self.inventory[shirt_type].remove(shirt_color)

    def daily_fit(self):
        """Return message with daily outfit details."""
        daily_fit = ""
        # If it's Sunday morning, return the weekly preview.
        if self.today == "Sunday" and time_of_day() == "morning":
            return self.weekly_preview()
        # If schedule does not exist.
        elif not isinstance(self.schedule, dict):
            daily_fit = self.schedule
        # If value is not dictionary, return the string.
        elif not isinstance(self.schedule[self.today], dict) or isPTO(self.curr_date):
            daily_fit = self.schedule[self.today]
        else:
            self.double_check_boots()
            boots = self.schedule[self.today]["boots"].title()
            chinos = self.schedule[self.today]["chinos"].title()
            belt = self.schedule[self.today]["belt"].title()
            self.double_check_shirt()
            # If shirt type is button_down, reformat to Button Down
            if "button_down" in self.schedule[self.today]["shirt"]:
                shirt = (self.schedule[self.today]["shirt"].split()[0] + " " + self.schedule[self.today]["shirt"].split()[1].replace("_", " ")).title()
            else:
                shirt = self.schedule[self.today]["shirt"].title()
            jacket = self.schedule[self.today]["jacket"].title()
            # Build HTML string to feed to emailer.
            daily_fit = f"<i>Boots:</i> {boots}<br><i>Chinos:</i> {chinos}<br><i>Belt:</i> {belt}<br><i>Shirt:</i> {shirt}<br><i>Jacket: </i>{jacket}<br>"
            # Update the schedule in case any changes were made.
            self.save_schedule()
        return daily_fit
        
    def weekly_preview(self):
        """Pull the whole generated schedule to send for the weekly preview."""
        preview = ""
        shirt = ""
        for key, value in self.schedule.items():
            if key != "Saturday" and key != "Sunday":
                if isinstance(value, dict):
                    boots = value["boots"].title()
                    chinos = value["chinos"].title()
                    belt = value["belt"].title()
                    # If shirt type is button_down, reformat to Button Down
                    if "button_down" in value["shirt"]:
                        shirt = (value["shirt"].split()[0] + " " + value["shirt"].split()[1].replace("_", " ")).title()
                    else:
                        shirt = value["shirt"].title()
                    jacket = value["jacket"].title()
                    preview += f"<u><b>{key}</b></u><br><i>Boots:</i> {boots}<br><i>Chinos:</i> {chinos}<br><i>Belt:</i> {belt}<br><i>Shirt:</i> {shirt}<br><i>Jacket: </i>{jacket}<br><br>"
                else:
                    preview += f"<u><b>{key}</b></u><br>{value}<br><br>"
        return preview

    def run(self):
        """Run the wardrobe module."""
        # Only run the module for the morning briefing.
        if time_of_day() == "morning":
            self.load_config()
            if self.load_forecast():
                self.parse_forecast()
                # If Sunday, build the weekly schedule.
                if self.today == "Sunday":
                    self.get_template()
                    self.prioritize_days()
                    self.build_days()
                    self.save_schedule()
                else:
                    if self.load_schedule():
                        self.update_inventory()
                return self.daily_fit()
            else:
                return "Forecast does not exist."
        # Skip running the module and return none because midday briefing doesn't include wardrobe.
        else:
            return None
        
    def preview_update(self):
        """Test sending the weekly preview."""
        from alerts import send_email
        self.load_schedule()
        preview = self.weekly_preview()
        email = send_email.Emailer(
            forecast=None, 
            wardrobe=preview, 
            news=None, 
            cves=None
            )
        email.run_update("preview")

    def manual_run(self):
        """Testing ground."""
        self.load_config()
        if self.load_forecast():
            self.parse_forecast()
            # --- #
            self.get_template()
            self.prioritize_days()
            self.build_days()
            self.save_schedule()
            # self.preview_update()
        

if __name__ == "__main__":
    ### Testing ####
    gen = WardrobeGenerator()
    print(gen.run())

