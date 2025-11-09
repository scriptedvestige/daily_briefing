#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.time_utils import filename_format, filename_delta, iso_format, iso_delta, time_of_day
from utils.file_utils import config_path, news_out, check_file
import requests
import json
import os


class CveScraper():
    """This module scrapes CVEs from multiple NIST API endpoints."""
    def __init__(self):
        self.config = config_path("cve")
        # Dates
        self.time_of_day = time_of_day()
        self.file_date = filename_format()
        self.file_yesterday = filename_delta(-1)
        self.today_search = f"{iso_format()}T23:59:59.999"
        self.yesterday_search = f"{iso_delta(-1)}T00:00:00.000"
        # Config
        self.url = ""
        self.endpoints = []
        self.keywords = []
        self.prev_out = []
        self.cves = {"morning": {}, "midday": {}}
        self.cves_out = ""
    
    def load_config(self):
        """Load the config."""
        with open(self.config, "r") as file:
            full_config = json.load(file)
            self.url = full_config["url"]
            self.endpoints = full_config["endpoints"]
            self.keywords = full_config["keywords"]

    def load_cves(self, date):
        """Load previously sent CVEs."""
        data = {}
        filename = f"cve_check_{date}.json"
        filepath = os.path.join(self.output_dir, filename)
        if check_file(filepath) and date == self.file_date and time_of_day() == "midday" and len(data["morning"].values()) > 0:
            for key, value in data["morning"].items():
                self.cves["morning"][key] = value
        if check_file(filepath):
            with open(filepath, "r") as file:
                data = json.load(file)
            self.prev_output(data)
    
    def prev_output(self, data):
        """Build the output variable with data loaded from files or pulled from the API endpoints."""
        for item in data.keys():
            if len(item) > 0:
                for entry in data[item].keys():
                    self.prev_out.append(entry)

    def set_parameters(self, endpoint):
        """Set the parameters for the call."""
        start = f"{endpoint}StartDate"
        end = f"{endpoint}EndDate"
        params = {
            start: self.yesterday_search,
            end: self.today_search
        }
        return params
        
    def make_call(self, params):
        """Call the API given the URL and parameters."""
        r = requests.get(self.url, params)
        return r.json()
    
    def parse_data(self, data):
        """Parse the data returned by the API call."""
        vulns = []
        if data["totalResults"] > 0:
            vulns = data["vulnerabilities"]
        for values in vulns:
            cve_status = values["cve"]["vulnStatus"]
            cve_id = values["cve"]["id"]
            cve_source = values["cve"]["sourceIdentifier"]
            cve_desc = values["cve"]["descriptions"][0]["value"]
            cve_metrics = values["cve"]["metrics"]
            # Check whether keywords from config are present in description and CVE status is analyzed.
            if self.check_keywords(desc=cve_desc, source=cve_source) and self.check_metrics(cve_metrics) and self.check_duplicate(cve_id) and cve_status == "Analyzed":
                    cvss_key = next(iter(cve_metrics))
                    cvss_sev = cve_metrics[cvss_key][0]["cvssData"]["baseSeverity"]
                    cvss_score = cve_metrics[cvss_key][0]["cvssData"]["baseScore"]
                    # If severity is high or critical.
                    if cvss_sev == "HIGH" or cvss_sev == "CRITICAL":
                        self.cves[self.time_of_day][cve_id] = {"Description": cve_desc, "Severity": cvss_sev, "Score": cvss_score}

    def check_keywords(self, desc, source):
        """Check if keywords are present in description."""
        for word in self.keywords:
            if word.lower() in desc.lower() or word.lower() in source.lower():
                return True
            else:
                continue

    def check_metrics(self, entry):
        """Check that the metrics section is a dictionary and is not empty."""
        if isinstance(entry, dict) and len(entry) > 0:
            return True
        else:
            return False

    def check_duplicate(self, entry):
        """Check if CVE has already been saved."""
        if entry not in self.prev_out:
            return True
        else:
            return False
        
    def sort_cvss(self):
        """Sort the CVE dictionary so that highest scores are listed first."""
        selected = self.cves.get(self.time_of_day, {})
        sorted_cves = dict(sorted(selected.items(), key=lambda item: item[1]["Score"], reverse=True))
        self.cves[self.time_of_day] = sorted_cves

    def save_output(self):
        """Save the parsed output to a JSON file."""
        filename = f"cve_check_{self.file_date}.json"
        filepath = os.path.join(news_out(), filename)
        with open(filepath, "w") as file:
            json.dump(self.cves, file, indent=4)

    def format_data(self, time):
        """Format data to feed to emailer module."""
        if len(self.cves[time]) > 0:
            for key, item in self.cves[time].items():
                id = key
                sev = item["Severity"]
                score = item["Score"]
                desc = item["Description"]
                self.cves_out += f"<a href='https://nvd.nist.gov/vuln/detail/{id}' target='_blank'>{id}</a><br>Severity: {sev} / {score}<br>{desc}<br><br>"
        else:
            self.cves_out = "No new CVEs."
        return self.cves_out

    def run(self):
        """Run the module."""
        self.load_config()
        self.load_cves(self.file_yesterday)
        if self.time_of_day == "midday":
            self.load_cves(self.file_date)
        for entry in self.endpoints:
            params = self.set_parameters(entry)
            data = self.make_call(params)
            self.parse_data(data)
        self.sort_cvss()
        self.save_output()
        return self.format_data(self.time_of_day)


if __name__ == "__main__":
    cve = CveScraper()
    cve.run()

