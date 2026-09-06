#!/usr/bin/env python3

from utils.time_utils import filename_format, filename_delta, day_name, time_of_day
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

    def extract_date(self, filename):
        """Pull the YYYYMMDD date out of a filename, or return None if it doesn't match the expected pattern."""
        stem = filename.split("_")[-1]
        if not stem.endswith(".json"):
            return None
        candidate = stem[:-5]
        if len(candidate) == 8 and candidate.isdigit():
            return candidate
        return None

    def clean_dirs(self, keep_dates):
        """Remove files in all output dirs whose date isn't in keep_dates. Files that don't match the expected naming pattern are left alone."""
        removed = 0
        skipped = 0
        for directory in self.all_dirs:
            for filename in os.listdir(directory):
                full_path = os.path.join(directory, filename)
                if not os.path.isfile(full_path):
                    continue
                file_date = self.extract_date(filename)
                if file_date is None:
                    # Doesn't match the expected naming pattern — leave it alone rather than guess.
                    skipped += 1
                    continue
                if file_date not in keep_dates:
                    os.remove(full_path)
                    removed += 1
        print(f"[Cleaner] Removed {removed} old file(s), skipped {skipped} unrecognized file(s).")

    def run(self):
        """Run the cleaner. Only runs on Saturday morning."""
        if self.today == "Saturday" and time_of_day() == "morning":
            self.clean_dirs(keep_dates=(filename_format(), filename_delta(-1)))

    def manual_run(self):
        """Manually run the cleaner, keeping only today's files."""
        self.clean_dirs(keep_dates=(filename_format(),))


if __name__ == "__main__":
    janitor = CleanUp()
    janitor.manual_run()
