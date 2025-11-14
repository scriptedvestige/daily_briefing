#!/usr/bin/env python3

from utils.time_utils import filename_format, day_name, time_of_day
from utils.file_utils import alerts_out, news_out, wardrobe_out, weather_out
import os


class CleanUp():
    """
    Clean up old files in the output directories of the various modules.
    No...I clean...
    """
    def __init__(self):
        # Date
        self.today = day_name()
        # Paths
        self.all_dirs = [alerts_out(), news_out(), wardrobe_out(), weather_out()]

    def run(self):
        """Run the cleaner."""
        # Only run on Saturday morning.
        if self.today == "Saturday" and time_of_day() == "morning":
            for dir in self.all_dirs:
                # Grab all filenames in directory.
                all_files = os.listdir(dir)
                for file in all_files:
                    """
                    Get the file date from the file name.
                    Doing it this way is simpler because the date is in the name so it requires no imports or time format conversions.
                    """
                    file_date = file.split("_")[-1][:-5]
                    # If file date is older than current date, delete the file after ensuring it exists.
                    if file_date != filename_format():
                        full_path = os.path.join(dir, file)
                        if os.path.exists(full_path):
                            os.remove(full_path)

    def manual_run(self):
        """Manually run the cleaner."""
        for dir in self.all_dirs:
            # Grab all filenames in directory.
            all_files = os.listdir(dir)
            for file in all_files:
                """
                Get the file date from the file name.
                Doing it this way is simpler because the date is in the name so it requires no imports or time format conversions.
                """
                file_date = file.split("_")[-1][:-5]
                # If file date is older than current date, delete the file after ensuring it exists.
                if file_date != filename_format():
                    full_path = os.path.join(dir, file)
                    if os.path.exists(full_path):
                        os.remove(full_path)


if __name__ == "__main__":
    janitor = CleanUp()
    janitor.manual_run()
