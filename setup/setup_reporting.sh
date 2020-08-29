#!/bin/bash

SSDPATH=$1
DEVICE_ID=$2
DEVICE_NAME=$3
REPORT_TIME=$4

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
REPCONF="/home/trainspotting/scripts/config/reporting_config.R"
search="output_path="
replace="output_path='${SSDPATH}/trainspotting/'\n# output_path="
sudo sed -i "s~${search}~${replace}~g" $REPCONF

search="device_id="
replace="device_id=${DEVICE_ID}\n# device_id="
sudo sed -i "s~${search}~${replace}~g" $REPCONF

search="device_name="
replace="device_name='${DEVICE_NAME}'\n# device_id="
sudo sed -i "s~${search}~${replace}~g" $REPCONF
##############################################################

# 4. Setup cron job/tab
chmod u+x /home/trainspotting/services/run_reporting.service
sudo crontab -l > tabs
sudo echo "$REPORT_TIME * * * /home/trainspotting/services/run_reporting.service >> ${SSDPATH}/trainspotting/service_logs/run_reporting_service.log 2>&1" >> tabs
sudo crontab tabs
sudo rm tabs
#############################################################
