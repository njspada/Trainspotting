#!/bin/bash
# 1. install python3, pip3, curl
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.8
sudo apt-get install curl
sudo apt install python3-pip

# 2. Find external ssd path
SSDPATH=$(sudo lsblk | grep /media* | rev | cut -d' ' -f1 | rev)
echo "ssd_path <- ${SSDPATH}" > /home/trainspotting/ssd_path.R
export SSDPATH
##############################################################

# 3. Install & configure MySQL
sudo chmod u+x setup_mysql.sh
sudo ./setup_mysql.sh
##############################################################

# 4. setup weewx
sudo chmod u+x setup_weewx.sh
sudo ./setup_weewx.sh
##############################################################

# 5. Setup utils for run_camera
sudo chmod u+x setup_camera.sh
sudo ./setup_camera.sh
##############################################################

# 6. Setup utils for run_purple_air
sudo chmod u+x setup_purple_air.sh
sudo ./setup_purple_air.sh
##############################################################

# 7. Setup utils for run_reporting
sudo chmod u+x setup_reporting.sh
sudo ./setup_reporting.sh
##############################################################

