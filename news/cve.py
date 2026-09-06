#!/usr/bin/env python3
# This is a hacky solution for manually testing individual modules.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from utils.time_utils import filename_format, filename_delta, iso_format, iso_delta, time_of_day
from utils.file_utils import config_path, check_file, cve_check_path
import requests
import json


def local_utc_offset():
    """Return current local UTC offset in ISO 8601 format (e.g. -07:00), accounting for DST automatically."""
    offset = datetime.now().astimezone().strftime("%z")  # e.g. "-0700"
    return f"{offset[:3]}:{offset[3:]}"


class CveScraper():
    """This module scrapes CVEs from multiple NIST API endpoints."""
    def __init__(self):
        self.config = config_path("cve")
        # Dates
        self.time_of_day = time_of_day()
        self.file_date = filename_format()
        self.file_yesterday = filename_delta(-1)
        self.today_search = f"{iso_format()}T23:59:59.999{local_utc_offset()}"
        self.yesterday_search = f"{iso_delta(-1)}T00:00:00.000{local_utc_offset()}"
        # Config
        self.url = ""
        self.endpoints = []
        self.keywords = []
        self.prev_out = []
        self.cves = {"morning": {}, "midday": {}}
        self.cves_out = ""
        self.keyword_hit = ""
        # Resilience tracking
        self.skipped_endpoints = 0
    
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
        filepath = cve_check_path(date)
        if check_file(filepath):
            with open(filepath, "r") as file:
                data = json.load(file)
            self.prev_output(data, date)

    def prev_output(self, data, date):
        """Build the output variable with data loaded from files or pulled from the API endpoints."""
        if date == self.file_date and time_of_day() == "midday" and len(data["morning"].values()) > 0:
            for key, value in data["morning"].items():
                self.cves["morning"][key] = value
        for item in data.keys():
            if len(data[item]) > 0:
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
        response = requests.get(self.url, params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    def parse_data(self, data, endpoint):
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
            if self.check_keywords(desc=cve_desc, source=cve_source) and self.check_metrics(cve_metrics) and self.check_duplicate(cve_id) and self.check_status(cve_status):
                    cvss_key = next(iter(cve_metrics))
                    cvss_sev = cve_metrics[cvss_key][0]["cvssData"]["baseSeverity"]
                    cvss_score = cve_metrics[cvss_key][0]["cvssData"]["baseScore"]
                    # If severity is high or critical.
                    if cvss_sev == "HIGH" or cvss_sev == "CRITICAL":
                        self.cves[self.time_of_day][cve_id] = {
                            "endpoint": endpoint,
                            "keyword": self.keyword_hit.title(), 
                            "description": cve_desc, 
                            "severity": cvss_sev, 
                            "score": cvss_score
                            }

    def check_keywords(self, desc, source):
        """Check if keywords are present in description."""
        self.keyword_hit = ""
        desc_l = desc.lower()
        source_l = source.lower()
        for word in self.keywords:
            w = word.lower()
            if w in desc_l or w in source_l:
                self.keyword_hit = w
                return True
        return False

    def check_metrics(self, entry):
        """Check that the metrics section is a dictionary and is not empty."""
        if isinstance(entry, dict) and len(entry) > 0:
            return True
        else:
            return False
        
    def check_status(self, status):
        """Check that the status of the entry is not received or rejected."""
        if status == "Analyzed" or status == "Awaiting Analysis" or status == "Undergoing Analysis":
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
        sorted_cves = dict(sorted(selected.items(), key=lambda item: item[1]["score"], reverse=True))
        self.cves[self.time_of_day] = sorted_cves

    def save_output(self):
        """Save the parsed output to a JSON file."""
        filepath = cve_check_path(self.file_date)
        with open(filepath, "w") as file:
            json.dump(self.cves, file, indent=4)

    def format_data(self, time):
        """Format data to feed to emailer module."""
        if len(self.cves[time]) > 0:
            for key, item in self.cves[time].items():
                id = key
                sev = item["severity"]
                score = item["score"]
                keyword = item["keyword"]
                desc = item["description"]
                if item["endpoint"] == "kev":
                    status = "Exploited in the Wild"
                elif item["endpoint"] == "pub":
                    status = "Newly Discovered"
                else:
                    status = "Updated"
                self.cves_out += f"<a href='https://nvd.nist.gov/vuln/detail/{id}' target='_blank'>{id}</a><br>Status: <b>{status}</b><br>Severity: {sev} / {score}<br>Keyword: {keyword}<br>{desc}<br><br>"
        else:
            self.cves_out = "It's quiet...too quiet...<br><br>"
        return self.cves_out

    def run(self):
        """Run the module."""
        self.load_config()
        self.load_cves(self.file_yesterday)
        if self.time_of_day == "midday":
            self.load_cves(self.file_date)
        for entry in self.endpoints:
            try:
                params = self.set_parameters(entry)
                data = self.make_call(params)
                self.parse_data(data, entry)
            except Exception:
                # If one endpoint fails or returns something unexpected, skip it — the rest still run.
                self.skipped_endpoints += 1
                continue
        self.sort_cvss()
        self.save_output()
        print(f"[CVE] Endpoints skipped: {self.skipped_endpoints}/{len(self.endpoints)} | CVEs matched: {len(self.cves[self.time_of_day])}")
        return self.format_data(self.time_of_day)


if __name__ == "__main__":
    cve = CveScraper()
    data = cve.run()
