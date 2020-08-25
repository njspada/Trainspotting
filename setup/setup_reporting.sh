#!/bin/bash
# 1. install R for ubuntu
sudo apt-get install aptitude
sudo aptitude install r-base
##############################################################

# 2. install reqs
echo "install.packages('tidyverse',repos = 'http://cran.us.r-project.org')" | R --no-save --silent
echo "install.packages('DBI',repos = 'http://cran.us.r-project.org')" | R --no-save --silent
echo "install.packages('RMariaDB',repos = 'http://cran.us.r-project.org')" | R --no-save --silent
##############################################################

# 3. update config
REPCONF="/home/trainspotting/Trainspotting/scripts/config/reporting_config.R"
mv "$REPCONF" "$REPCONF.bak"
cat "$REPCONF.bak" | grep -v "^output_path=" > "$REPCONF"
echo "output_path=${SSDPATH}/trainspotting/" >> "$REPCONF"
##############################################################

# 4. Setup cron job/tab
chmod u+x /home/trainspotting/Trainspotting/services/run_reporting.sh
sudo crontab -l > tabs
echo "55 23 * * * /home/trainspotting/Trainspotting/services/run_reporting.sh"
##############################################################