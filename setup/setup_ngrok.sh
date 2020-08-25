#!/bin/bash

# 1. download ngrok
sudo cd /home/trainspotting
sudo curl https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip -o ngrok_archive.zip
unzip ngrok_archive.zip
chmod u+x ngrok
##############################################################

# 2. update config file
sudo cd Trainspotting/scripts/config
search="log:"
replace="log: ${SSDPATH}/trainspotting/service_logs/ngrok.log"
sudo sed -i 's#${search}#${replace}#g' ngrok_config.yml
##############################################################

# 3. setup ngrok service
sudo cd /home/trainspotting/Trainspotting/services
sudo cp run_ngrok.service /etc/systemd/system
sudo chmod /etc/systemd/system/run_ngrok.service
##############################################################