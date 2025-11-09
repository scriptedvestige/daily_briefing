#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.time_utils import day_name, filename_format, time_of_day, briefing_message_date, current_date_time
from utils.file_utils import briefing_template, preview_template, sent_brief_title, sent_preview_title, config_path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from alerts.encryption import Encryptor
import smtplib, ssl
import time
import gc


class Emailer:
    """Inject the data into the appropriate template and send briefing via email."""
    def __init__(self, forecast, wardrobe, news, cves):
        self.config = config_path("smtp")
        # Time
        self.today = day_name()
        self.file_date = filename_format()
        self.time_of_day = time_of_day()
        self.timestamp = f"Generated {current_date_time()}"
        # Files
        self.briefing_template = briefing_template(self.time_of_day)
        self.preview_template = preview_template()
        self.briefing_send = sent_brief_title(self.time_of_day, self.file_date)
        self.preview_send = sent_preview_title(self.file_date)
        # Data
        self.forecast = forecast
        self.wardrobe = wardrobe
        self.news = news
        self.cves = cves
        # Email Config
        self.server = ""
        self.port = ""
        self.sender = ""
        self.auth = ""
        self.receiver = ""

    def load_config(self):
        """Load the config file."""
        enc = Encryptor()
        full_config = enc.decrypt()
        self.server = full_config["server"]
        self.port = full_config["port"]
        self.sender = full_config["from"]
        self.auth = full_config["pass"]
        self.receiver = full_config["to"]

    def select_template(self, filepath):
        """Select appropriate briefing template based on time of day."""
        with open(filepath, "r") as file:
            body = file.read()
        return body
    
    def inject_data(self, template, filepath):
        """Inject the data into the template."""
        wardrobe = ""
        if "preview" not in filepath:
            wardrobe = "Check the weekly wardrobe preview!"
        else:
            wardrobe = self.wardrobe
        return template.format(
                date = briefing_message_date(),
                forecast = self.forecast,
                wardrobe = wardrobe,
                news = self.news,
                cves = self.cves,
                timestamp = self.timestamp
        )
    
    def save_sent_email(self, filepath, email):
        """Save the output from inject_data to file."""
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(email)

    def send_email(self, email, title):
        """Send it!"""
        # Build messages.
        message = MIMEMultipart("alternative")
        message["Subject"] = title
        message["From"] = self.sender
        message["To"] = self.receiver
        # Set email content.
        html = email
        message.attach(MIMEText(html, "html"))
        # Establish connection.
        context = ssl.create_default_context()
        with smtplib.SMTP(self.server, self.port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(self.sender, self.auth)
            server.sendmail(self.sender, self.receiver, message.as_string())

    def clean_vars(self):
        """Clear RAM of variables with sensitive data."""
        self.server = None
        self.port = None
        self.sender = None
        self.auth = None
        self.receiver = None
        gc.collect()

    def run(self):
        """Ingest data from other modules, inject into appropriate template, send email."""
        self.load_config()
        template = self.select_template(self.briefing_template)
        email = self.inject_data(template, self.briefing_template)
        self.save_sent_email(filepath=self.briefing_send, email=email)
        brief_title = f"{self.time_of_day.title()} Briefing {self.file_date}"
        self.send_email(email=email, title=brief_title)
        # Send the weekly preview also if it is Sunday morning.
        if self.today == "Sunday" and self.time_of_day == "morning":
            preview_template = self.select_template(self.preview_template)
            preview_email = self.inject_data(preview_template, self.preview_template)
            self.save_sent_email(filepath=self.preview_send, email=preview_email)
            preview_title = f"Weekly Wardrobe Preview {self.file_date}"
            self.send_email(email=preview_email, title=preview_title)
            self.clean_vars()

    def run_update(self, type):
        """Run the module for a test."""
        self.load_config()
        template = ""
        path = ""
        if type.lower() == "preview":
            template = self.preview_template
            path = self.preview_send
        else:
            template = self.briefing_template
            path = self.briefing_send
        selected_template = self.select_template(template)
        update_email = self.inject_data(selected_template, template)
        self.save_sent_email(filepath=path, email=update_email)
        update_title = f"{type.title()} Update {self.file_date}"
        self.send_email(email=update_email, title=update_title)
        self.clean_vars()


if __name__ == "__main__":
    ### Testing ###
    # Create instance of wardrobe module, tell it to load weekly schedule and return weekly preview.
    from wardrobe import generator
    gen = generator.WardrobeGenerator()
    gen.load_schedule()
    preview = gen.weekly_preview()
    # Send updated weekly preview.
    email = Emailer(forecast=None, wardrobe=preview, news=None, cves=None)   
    email.run_update("preview")
