#!/usr/bin/env python3
# This is a hacky solution for manually testing individual modules.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.time_utils import day_name, time_of_day, filename_format, filename_delta, future_dayname, is_pto, iso_format
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
        self.original_rules = {}
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
        with open(self.config_path, "r") as file:
            self.inventory = json.load(file)
        self.temp_rules = self.inventory["rules"]["temp"]
        self.precip_rules = self.inventory["rules"]["precip"]
        self.original_rules = json.loads(json.dumps(self.inventory["rules"]))

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
        for entry in self.weekly_fc:
            date = entry["startTime"].split("T")[0]
            dayname = future_dayname(date)
            if entry["isDaytime"] and dayname in self.workdays:
                temp = entry["temperature"]
                precip = entry["probabilityOfPrecipitation"]["value"]
                wind = int(entry["windSpeed"].split()[-2])
                feels_like = self.feels_like_temp(raw_temp=temp, wind_speed=wind)
                self.parsed_fc[dayname] = {"date":date, "temp":temp, "feelsLike":feels_like, "precip":precip, "wind":wind}

    def get_template(self):
        """Load the template to build the schedule."""
        with open(self.schedule_template, "r") as template:
            self.schedule = json.load(template)

    def check_temp_range(self, temp, shirts, pants):
        """Check the temp value from the forecast against the ranges for shirts."""
        for i, (low, high) in enumerate(self.temp_rules["range"]):
            if low <= temp <= high:
                shirt = shirts[i]
                pant = pants[i]
                return {"shirt_type": shirt, "pant_type":pant}

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
            shirt_pant = self.check_temp_range(temp=self.parsed_fc[day]["feelsLike"], shirts=self.temp_rules["shirt"], pants=self.temp_rules["pants"])
            # Score the day for it's priority and add to dictionary.
            self.priority[day] = [self.day_score(temp_score=self.temp_score(
                shirt_type=shirt_pant["shirt_type"], feels_like=self.parsed_fc[day]["feelsLike"]), 
                precip_score=self.precip_score(self.parsed_fc[day]["precip"])
                ),
                shirt_pant["shirt_type"],
                shirt_pant["pant_type"]]
        # Sort the priority dictionary.
        self.priority = dict(sorted(self.priority.items(), key=lambda item: item[1][0]))

    def build_days(self):
        """Choose the items for the given day."""
        for day in self.priority:
            if not is_pto(self.parsed_fc[day]["date"]):
                pant_type = self.priority[day][2]
                boot_type = self.check_precip_range(precip=self.parsed_fc[day]["precip"], boots=self.precip_rules["boots"])
                boot_color = self.choose_boots(boot_type).split()[0]
                chino_choices = self.inventory["rules"]["boots"][boot_color][pant_type]
                if not chino_choices:
                    boot_color = self.retry_boots(boot_type, pant_type)
                    if boot_color is None:
                        self.schedule[day] = "No compatible outfit left this week — chino inventory exhausted."
                        continue
                    chino_choices = self.inventory["rules"]["boots"][boot_color][pant_type]
                shirt = self.choose_chinos(boots=boot_color, chino_choices=chino_choices, shirt=self.priority[day][1], day=day, pant_type=pant_type)
                shirt_choice = self.choose_shirt(shirt_type=shirt, day=day, pant=pant_type)
                if shirt_choice is None:
                    continue
                self.remove_shirt(shirt_type=shirt, shirt_choice=shirt_choice)
                self.need_jacket(day)
            else:
                self.schedule[day] = "No work today!"

    def choose_boots(self, boots):
        """Choose boots for a given day."""
        if boots == "dry":
            boots = random.choice(self.inventory["dry_boots"])
        else:
            boots = random.choice(self.inventory["wet_boots"])
        return boots

    def retry_boots(self, boot_type, pant_type):
        """Choose a new boot color that still has available chino options for the given pant type,
        used when the first pick has run out of compatible chinos for this pant type."""
        pool = self.inventory["dry_boots"] if boot_type == "dry" else self.inventory["wet_boots"]
        candidates = [b for b in pool if self.inventory["rules"]["boots"][b][pant_type]]
        if not candidates:
            return None
        return random.choice(candidates)

    def choose_chinos(self, boots, chino_choices, shirt, day, pant_type):
        """Choose the color chinos and return shirt type."""
        shirt_type = ""
        # If no button downs left, choose flannel instead.
        if shirt == "button_down" and len(self.inventory[shirt]) == 0:
            shirt_type = "flannel"
        else:
            shirt_type = shirt
        chino_choice = random.choice(chino_choices)
        self.remove_chinos(pant_type=pant_type, chinos=chino_choice)
        # Save boot color and chinos to schedule for the given day
        self.schedule[day]["boots"] = boots
        self.schedule[day]["chinos"] = chino_choice
        self.choose_belt(boots=boots, day=day)
        return shirt_type

    def remove_chinos(self, chinos, pant_type):
        """Remove the selected chinos from all lists in inventory."""
        if chinos in self.inventory[pant_type]:
            self.inventory[pant_type].remove(chinos)
        # Remove chino option from every boot rule
        for key in self.inventory["rules"]["boots"].keys():
            if chinos in self.inventory["rules"]["boots"][key][pant_type]:
                self.inventory["rules"]["boots"][key][pant_type].remove(chinos)

    def add_chinos(self, chinos, pant_type):
        """Undo remove_chinos: restore item to top-level inventory and every boot rule that originally allowed it."""
        if chinos not in self.inventory[pant_type]:
            self.inventory[pant_type].append(chinos)
        for key in self.inventory["rules"]["boots"].keys():
            if chinos in self.original_rules["boots"][key][pant_type] and chinos not in self.inventory["rules"]["boots"][key][pant_type]:
                self.inventory["rules"]["boots"][key][pant_type].append(chinos)

    def choose_belt(self, boots, day):
        """Choose the appropriate belt for the day."""
        if boots == "charcoal_logger" or boots == "brown_logger":
            self.schedule[day]["belt"] = "canyon"
        elif boots == "pecan_douglas":
            self.schedule[day]["belt"] = "tan"
        else:
            self.schedule[day]["belt"] = "black"

    def choose_shirt(self, shirt_type, day, pant):
        """Choose a shirt color based on chino color."""
        shirt = ""
        if shirt_type == "button_down" and len(self.inventory[shirt_type]) == 0:
            shirt = "flannel"
        else:
            shirt = shirt_type
        chino_color = self.schedule[day]["chinos"]
        chino_rules = self.inventory["rules"][pant][chino_color]
        if shirt == "button_down" and chino_color == "black" and "black" not in chino_rules:
            chino_rules.append("black")
        shirt_options = [x for x in self.inventory[shirt] if x.split("/")[0] in chino_rules]
        if len(shirt_options) > 0:
            shirt_choice = random.choice(shirt_options)
        else:
            shirt_choice = self.retry_choices(chino=chino_color, shirt=shirt, day=day, pant_type=pant)
            if shirt_choice is None:
                return None
        self.schedule[day]["shirt"] = f"{shirt_choice} {shirt}"
        return shirt_choice
    
    def need_jacket(self, day):
        """Determine whether jacket is necessary."""
        if self.parsed_fc[day]["precip"] >= 30:
            self.schedule[day]["jacket"] = "yes"
        elif self.parsed_fc[day]["feelsLike"] <= 55:
            self.schedule[day]["jacket"] = "yes"
        else:
            self.schedule[day]["jacket"] = "no"

    def remove_shirt(self, shirt_type, shirt_choice):
        """Remove chosen shirt from inventory."""
        if shirt_choice in self.inventory[shirt_type]:
            self.inventory[shirt_type].remove(shirt_choice)

    def retry_choices(self, chino, shirt, day, pant_type):
        """If no options available for item, choose new item."""
        boot_color = self.schedule[day]["boots"]
        chino_choices = self.inventory["rules"]["boots"][boot_color][pant_type].copy()
        if not chino_choices:
            boot_type = self.check_precip_range(precip=self.parsed_fc[day]["precip"], boots=self.precip_rules["boots"])
            new_boot_color = self.retry_boots(boot_type, pant_type)
            if new_boot_color is None:
                self.schedule[day] = "No compatible outfit left this week — chino inventory exhausted."
                return None
            boot_color = new_boot_color
            chino_choices = self.inventory["rules"]["boots"][boot_color][pant_type].copy()
        self.choose_chinos(boots=boot_color, chino_choices=chino_choices, shirt=shirt, day=day, pant_type=pant_type)
        new_shirt = self.choose_shirt(shirt_type=shirt, day=day, pant=pant_type)
        self.add_chinos(chinos=chino, pant_type=pant_type)
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
        if set(self.inventory["dry_boots"]) == set(self.inventory["wet_boots"]):
            return
        new_precip = self.parsed_fc[self.today]["precip"]
        new_temp = self.parsed_fc[self.today]["feelsLike"]
        boot_type = self.check_precip_range(precip=new_precip, boots=self.precip_rules["boots"])
        shirt_pant = self.check_temp_range(temp=new_temp, shirts=self.temp_rules["shirt"], pants=self.temp_rules["pants"])
        pant_type = shirt_pant["pant_type"]
        current_boots = self.schedule[self.today]["boots"]
        correct_pool = self.inventory[f"{boot_type}_boots"]
        if current_boots not in correct_pool:
            boot_color = self.choose_boots(boot_type)
            chino_choices = self.inventory["rules"]["boots"][boot_color][pant_type]
            if not chino_choices:
                boot_color = self.retry_boots(boot_type, pant_type)
                if boot_color is None:
                    return
                chino_choices = self.inventory["rules"]["boots"][boot_color][pant_type]
            self.schedule[self.today]["boots"] = boot_color
            if self.schedule[self.today]["chinos"] not in chino_choices:
                self.choose_chinos(boots=boot_color, chino_choices=chino_choices, shirt=shirt_pant["shirt_type"], day=self.today, pant_type=pant_type)
            self.choose_belt(boots=boot_color, day=self.today)

    def double_check_shirt(self):
        """Check updated forecast data and verify shirt is still appropriate."""
        new_temp = self.parsed_fc[self.today]["feelsLike"]
        # Get shirt type based on new temperature.
        shirt_pant = self.check_temp_range(temp=new_temp, shirts=self.temp_rules["shirt"], pants=self.temp_rules["pants"])
        shirt = shirt_pant["shirt_type"]
        # If new shirt is different than scheduled shirt, choose a different shirt.
        if shirt not in self.schedule[self.today]["shirt"] and len(self.inventory[shirt]) > 0:
            shirt_choice = self.choose_shirt(shirt_type=shirt, day=self.today, pant=shirt_pant["pant_type"])
            if shirt_choice is not None:
                self.remove_shirt(shirt_type=shirt_pant["shirt_type"], shirt_choice=shirt_choice)

    def update_inventory(self):
        """Update the inventory for the selected item for schedule rebuilds."""
        used_inventory = {}
        # Create a list of all items used in schedule.
        for key, value in self.schedule.items():
            if self.today != key and key != "Saturday" and key != "Sunday" and isinstance(value, dict):
                used_inventory[key] = value
        # Remove items used on other days from current inventory.
        for value in used_inventory.values():
            if value["chinos"] in self.inventory["bonobos"]:
                self.remove_chinos(chinos=value["chinos"], pant_type="bonobos")
            else:
                self.remove_chinos(chinos=value["chinos"], pant_type="kuhl")
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
        # If today isn't in the schedule at all.
        elif self.today not in self.schedule:
            daily_fit = "No schedule entry found for today."
        # If value is not dictionary, return the string.
        elif not isinstance(self.schedule[self.today], dict) or is_pto(self.curr_date):
            daily_fit = self.schedule[self.today]
        else:
            self.double_check_boots()
            boots = self.schedule[self.today]["boots"].replace("_", " ").title()
            chinos = self.schedule[self.today]["chinos"].title()
            belt = self.schedule[self.today]["belt"].title()
            self.double_check_shirt()
            self.need_jacket(self.today)
            # If shirt type is button_down, reformat to Button Down
            if "button_down" in self.schedule[self.today]["shirt"]:
                shirt = (self.schedule[self.today]["shirt"].replace("_", " ")).title()
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
                    boots = (value["boots"].replace("_", " ")).title()
                    chinos = value["chinos"].title()
                    belt = value["belt"].title()
                    # If shirt type is button_down, reformat to Button Down
                    if "button_down" in value["shirt"]:
                        shirt = (value["shirt"].replace("_", " ")).title()
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
    
    def rebuild_schedule(self):
        """Rebuild the schedule with new items."""
        self.load_config()
        if self.load_forecast():
            self.parse_forecast()
            self.get_template()
            self.prioritize_days()
            self.build_days()
            self.save_schedule()
        else:
            print("Error loading forecast.  Check forecast file exists.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rebuild or preview the wardrobe schedule.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rebuild", action="store_true", help="Rebuild the weekly schedule.")
    group.add_argument("--preview", action="store_true", help="Send a test of the weekly preview email.")
    args = parser.parse_args()

    gen = WardrobeGenerator()
    if args.rebuild:
        gen.rebuild_schedule()
    elif args.preview:
        gen.preview_update()

