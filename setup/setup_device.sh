#!/bin/bash

# -1. set noninteractive frontend
export DEBIAN_FRONTEND=noninteractive
##############################################################

# 0. git clone from production branch
sudo mkdir /home/trainspotting
sudo cd /home/trainspotting
sudo git clone --single-branch --branch production https://dmmajithia:3e4eda1c57ad3c97950c9fb2e02da56a1110b0dc@github.com/njspada/Trainspotting.git
##############################################################

# 1. install python3, pip3, curl
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.8
sudo apt-get install curl
sudo apt install python3-pip
##############################################################

# 2. Find external ssd path
SSDPATH=$(sudo lsblk | grep /media* | rev | cut -d' ' -f1 | rev)
echo "ssd_path <- ${SSDPATH}" > /home/trainspotting/ssd_path.R
export SSDPATH
##############################################################

# 3. Install & configure MySQL
sudo cd Trainspotting/setup
sudo chmod u+x setup_mysql.sh
sudo ./setup_mysql.sh
##############################################################

# 4. setup weewx
sudo cd Trainspotting/setup
sudo chmod u+x setup_weewx.sh
sudo ./setup_weewx.sh
##############################################################

# 5. Setup utils for run_camera
sudo cd Trainspotting/setup
sudo chmod u+x setup_camera.sh
sudo ./setup_camera.sh
##############################################################

# 6. Setup utils for run_purple_air
sudo cd Trainspotting/setup
sudo chmod u+x setup_purple_air.sh
sudo ./setup_purple_air.sh
##############################################################

# 7. Setup utils for run_reporting
sudo cd Trainspotting/setup
sudo chmod u+x setup_reporting.sh
sudo ./setup_reporting.sh
##############################################################

# 8. Setup ngrok
sudo cd Trainspotting/setup
sudo chmod u+x setup_ngrok.sh
sudo ./setup_ngrok.sh
##############################################################

# 9. Enable all services for auto start on boot
sudo systemctl enable weewx
sudo systemctl enable run_camera.service
sudo systemctl enable run_purple_air.service
sudo systemctl enable run_ngrok.service
##############################################################

echo "Done setup. Please check logs/output for any errors/mishaps."

