# Daily Briefing
The orchestrator run_briefing.py imports and runs all modules.  Due to the modular nature of the project, modules can be added or removed very easily in the orchestrator script.

The project is intended to be dropped on a device that has 24 hour uptime and scheduled to run with cron jobs for the two runs per day.  There is no GUI or text printed to the console, so this can be run headless, silently in the background.  The run.sh script will cd into the project directory and call the orchestrator and perform some basic logging in the cron.log file it drops.  This will contain start and finish times of each run, plus traceback if anything breaks.

This project has been built on Windows, so it is likely that when dropping it on a Linux device, the dos2unix command will need to be run.

This project only uses three packages that are not built in, see requirements.txt for versions and dependencies:
  - feedparser
  - requests
  - cryptography

To install the packages, activate your venv at the root directory of the project, then use the command "pip -r install requirements.txt".

This version of the project has been sanitized for obvious reasons, you'll need to do some configuration if you'd like to run this yourself.

Error handling and logging of errors is handled by the decorator function in the run_briefing.py orchestrator.

There is still some polishing to be done, that will come in time.

[Configurations](#configurations) |
[Templates](#templates) |
[Utils](#timeutils--fileutils) |
[Weather](#weather-module) |
[Wardrobe](#wardrobe-module) |
[News](#news-module) |
[CVEs](#cve-module) |
[Encryption](#encryption-module) |
[Email](#email-module) |
[Cleaner](#cleaner-module) |
[Use](#how-do-i-use-this)

---

### Configurations:
Configuration files are stored at path daily_briefing/configs.  Each module loads the data it needs from the corresponding config file.  Because of this, changing a weather source, news source, changing keywords to search for, or adding items to wardrobe inventory can be done without touching the code in the corresponding module.

---

### Templates:
Template files are stored at path daily_briefing/templates.  The emailer module injects data from the other modules in to the HTML templates.

---

### TimeUtils & FileUtils:
These modules live at daily_briefing/utils.  TimeUtils contains functions that provide dates and times in various formats to be used by all modules.  FileUtils functions build file paths to be used in all modules.

---

### Weather Module:
The weather module scrapes an NWS API endpoint and saves the weekly forecast data as a json at path daily_briefing/weather/output.  This data is formatted as a string containing HTML tags and returned to the corresponding variable in the orchestrator.

##### API URL
1. Calling the "/points/{latitude},{longitude}" endpoint gives you the parameters to plug into the gridpoints endpoint. 
2. For NWS data, the API endpoint being used is "/gridpoints/{officeID}/{x},{y}/forecast".   
3. The gridpoints endpoint then gives you the forecast data within a 2.5km grid area.

---

### Wardrobe Module:
**Warning: This module contains logic that is very customized!  If you intend to use this module, it will likely require heavy modification for proper function!**  

The wardrobe module loads the most current weather forecast file and parses the data to get what it needs.  The feels like temperature must be calculated.  On Sundays, the wardrobe generates a weekly schedule for work days and saves it as a json file at path daily_briefing/wardrobe/output.  When days are built, the pto_config.json file is checked, and if the day's date is not a PTO day, then items will be selected.  Boot type is chosen based on precipitation chance, shirt type is chosen based on feels like temperature.  Boot type and color determines acceptable pant color, pant color determines acceptable shirt color.  Wardrobe inventory and acceptable color pairings per item are stored in the configuration file.  Shirts and pants chosen are removed from the inventory after one use.

On work days, the module pulls the day's build from the schedule json file.  It double checks whether boot type and shirt type are still appropriate given the current day's forecast.  If choices are not acceptable, the module reloads the inventory and goes through the items chosen for all other days in the week, removes them from the inventory (shirts and pants), then rebuilds the current day.  The updated schedule overwrites the file that was saved on the previous Sunday.

On Sundays, the whole schedule is formatted as a string containing HTML tags to be sent in the weekly wardrobe preview HTML template.  All other days, the current day's build is formatted as a string containing HTML tags to be sent in the morning briefing.  Output is returned to the corresponding variable in the orchestrator module.

Wardrobe data is not included in the midday run of the briefing, so the module will pass and return None if time of day is midday.

---

### News Module:
The news module pulls the RSS feeds from the sources listed in the config file.  Each entry will be checked that the date matches either the current day or day prior.  Then the article title is checked for the keywords listed in the config.  Any article that matches those parameters is then checked agains previous runs to ensure an article isn't sent twice.  Output is saved to a json file at path daily_briefing/news/output, then formatted as a string containing HTML tags and returned to the corresponding variable in the orchestrator.

---

### CVE Module:
This module operates almost exactly like the news module, but uses the NIST CVE API endpoints for Known Exploited Vulnerabilities, Last Modified Date, and Published date.  The entries are filtered by keywords listed in the cve_config file, and IDs are checked to see if they've already been sent in previous runs.  The data is then saved in a json file at path daily_briefing/news/output, then formatted as a string containing HTML tags and returned to the corresponding variable in the orchestrator.

---

### Encryption Module:
Any config files that contain sensitive information should be encrypted.  For this project, that includes the smtp config as that json file contains credentials to authenticate for sending the emails.

The cryptography package uses symmetrical encryption.  You can keep the key whereever you like, just modify the appropriate variable with the path you'd like.

Prior to the first run, you should create a key and encrypt at least the smtp config.  The email module will import the encryption module and decrypt the smtp config file and store the config elements as variables in RAM.

The module will check that the key exists.  If the key does not exist, it will make a new key, then load the key.  If the key does exist, no new key is made and the key is loaded.  The smtp config file will be decrypted, but not overwritten.  The decrypted data is saved to variables, which are cleared after the email is sent.

---

### Email Module:
The orchestrator feeds all data returned by the other modules as HTML strings to the email module.  The email module selects the appropriate HTML template/s given day and time.  The template is stored as a variable and the data fed into the module is injected.  The rendered template is saved as an HTML file at path daily_briefing/alerts/output.

The module will then import the encryption module, decrypt the smtp config file and save the creds and settings as variables in RAM.

The email is sent over a TLS connection via the provider of your choice.  You'll need to look up the server for your provider.  Port will likely be 587, but double check that.  You will need to store your credentials for authentication to your provider in the smtp config file.  Make sure you encrypt this file!!!!!  If you have MFA enabled on your email login (which you should), you'll need to generate an application password to be used so the MFA doesn't cause issues.  The only part of this connection that is not encrypted is the initial handshake.

Once the email is sent, the module will set the variables that hold the smtp config data to None, then call garbage collector to clear that data from RAM.

---

### Cleaner Module:
Every Saturday morning this module will delete all files older than the current date in the following paths:
  - daily_briefing/alerts/output (Sent email HTML files)
  - daily_briefing/news/output (News and CVE JSON files)
  - daily_briefing/wardrobe/output (Weekly wardrobe schedule JSON files)
  - daily_briefing/weather/output (Weather forecast JSON files)

---

### How Do I Use This?
Some configuration will be necessary to run this project.  I've sanitized configurations and filepaths for obvious reasons.

- **Weather Module**: Use the instructions above to find the API endpoint for your location.
- **Wardrobe Module**: If you're brave enough, enter your clothing inventory and rules (think something like if pants are navy, acceptable shirt colors are ["grey", "black"] or whatever floats your boat).  I've included a warning previously that this may require heavy modification to use.  If you don't want to use it, delete it from the orchestrator and remove the module from the file structure.
- **News Module:** You'll need to grab the URLs for the RSS feeds of the sources you want to pull from.  Then enter the keywords that interest you in the list under key "keywords".
- **CVE Module:** For this one I've left the URL and API endpoints in the config file, simply enter the keywords you want to look for.
- **Encryption Module:** You'll need to run the key generation funcion and encrypt your SMTP config file manually before the first run.  (Or comment out the encryption part while testing.)
- **Email Module:** You'll need to configure the email module to use your provider and supply the credentials for the account you'll be using to send the emails.
- **Times:** Default for news and CVEs is current date and the day prior.  This can be modified, but you'll have to touch the code a smidge. (Maybe this should be moved into config files, idk).

Use scp in PowerShell to securely copy the project to your target location if you're moving the project from one box to another.

Once all of the appropriate modifications have been made, you might need to run dos2unix on it if you're dropping this on a Linux box.  I ran into a situation where I ran it the first time after I used scp to move it from my Windows box to the Pi I'm running it on.  The run.sh would work when running manually, but wouldn't work with cron.  I deleted the project, redid the scp, then set everything up again minus dos2unix.  Cron started working on the second attempt.  Your mileage may vary.

There is a run.sh bash script in the repo that you'll want to call with the cron jobs for Linux boxes.  Make sure you make the run.sh script executable, then test it to ensure it will run manually.  After that set up your scheduled tasks/cron jobs to execute run.sh.  The bash script will save start and finish messages to a file "cron.log" in the root of the project directory.  Set up logrotate to clear the logs on your preferred time frame.  I set mine to clear the log weekly.
