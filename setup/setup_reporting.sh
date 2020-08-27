#!/bin/bash

SSDPATH=$1

# 1. install R for ubuntu
sudo apt-get install -yq aptitude
sudo aptitude install -y -q r-base
##############################################################

# 2. install reqs
sudo apt-get install -yq libcurl4-openssl-dev
sudo apt-get install -yq libmysqlclient-dev
echo "install.packages('tidyverse',repos = 'http://cran.us.r-project.org')" | R --no-save --silent
echo "install.packages('DBI',repos = 'http://cran.us.r-project.org')" | R --no-save --silent
echo "install.packages('RMariaDB',repos = 'http://cran.us.r-project.org')" | R --no-save --silent
##############################################################

# 3. update config
REPCONF="/home/trainspotting/Trainspotting/scripts/config/reporting_config.R"
search="output_path="
replace="output_path='${SSDPATH}/trainspotting/'\n# output_path="
sudo sed -i "s~${search}~${replace}~g" $REPCONF
##############################################################

# 4. Setup cron job/tab
chmod u+x /home/trainspotting/Trainspotting/services/run_reporting.service
sudo crontab -l > tabs
sudo echo "55 23 * * * /home/trainspotting/Trainspotting/services/run_reporting.service >> ${SSDPATH}/trainspotting/service_logs/run_reporting_service.log 2>&1" >> tabs
sudo crontab tabs
sudo rm tabs
#############################################################
