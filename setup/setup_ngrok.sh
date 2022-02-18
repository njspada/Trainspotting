#!/bin/bash

SSDPATH=$1

# 1. download ngrok
cd /home/trainspotting
sudo curl https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm64.zip -o ngrok_archive.zip
unzip ngrok_archive.zip
chmod u+x ngrok
##############################################################

# 2. update config file
cd /home/trainspotting/scripts/config
search="log:"
replace="log: ${SSDPATH}/trainspotting/service_logs/ngrok.log"
sudo sed -i "s#${search}#${replace}#g" ngrok_config.yml
##############################################################

# 3. setup ngrok service
sudo cp /home/trainspotting/services/run_ngrok.service /etc/systemd/system
# sudo chmod u+x /etc/systemd/system/run_ngrok.service
##############################################################
