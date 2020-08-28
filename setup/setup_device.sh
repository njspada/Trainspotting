#!/bin/bash
# Before running setup do this:
#	- unplug coral usb
#	- plug in purple air usb
#	- plug in weewx usb
#	- plug in ssd usb
#	- reboot

# -2. set noninteractive frontend
export DEBIAN_FRONTEND=noninteractive
##############################################################

# -1. Set device name
echo -n "Enter a device name: "
read DEVICE_NAME
response=$(curl -i http://54.188.2.207/setup_device.php?name=$DEVICE_NAME)
DEVICE_ID=${response##*=}
DEVICE_ID=${DEVICE_ID%%;*}
FS="Failed to setup device name.\nPrinting response and exiting."
SS="Successfully setup device name. Device id=$DEVICE_ID."
if [[ -z $( echo "$response" | grep "200 OK" ) ]]; then echo 'Failed'; exit; else echo "$SS"; fi
EXPORT DEVICE_ID
EXPORT DEVICE_NAME

# 0. git clone from production branch
sudo mkdir /home/trainspotting
cd /home/trainspotting
sudo git clone --depth=1 --single-branch --branch production https://dmmajithia:3e4eda1c57ad3c97950c9fb2e02da56a1110b0dc@github.com/njspada/Trainspotting.git
sudo cp -rp Trainspotting/scripts /home/trainspotting
sudo cp -rp Trainspotting/setup /home/trainspotting
sudo cp -rp Trainspotting/services /home/trainspotting
##############################################################

# 1. install python3, pip3, curl
sudo apt-get update
sudo apt-get install -yq curl
sudo apt-get install -yq python3-pip
##############################################################

# 2. Find external ssd path
SSDPATH=$(sudo lsblk | grep /media* | rev | cut -d' ' -f1 | rev)
echo "ssd_path <- ${SSDPATH}" > /home/coal/Desktop/ssd_path.R
export SSDPATH
##############################################################

# 3. Install & configure MySQL
cd /home/trainspotting/setup
sudo chmod u+x setup_mysql.sh
sudo ./setup_mysql.sh $SSDPATH
##############################################################

# 4. setup weewx
cd /home/trainspotting/setup
sudo chmod u+x setup_weewx.sh
sudo ./setup_weewx.sh
##############################################################

# 5. Setup utils for run_camera
cd /home/trainspotting/setup
sudo chmod u+x setup_camera.sh
sudo ./setup_camera.sh $SSDPATH
##############################################################

# 6. Setup utils for run_purple_air
cd /home/trainspotting/setup
sudo chmod u+x setup_purple_air.sh
sudo ./setup_purple_air.sh
##############################################################

# 7. Setup utils for run_reporting
cd /home/trainspotting/setup
sudo chmod u+x setup_reporting.sh
sudo ./setup_reporting.sh $SSDPATH $DEVICE_ID $DEVICE_NAME
##############################################################

# 8. Setup ngrok
cd /home/trainspotting/setup
sudo chmod u+x setup_ngrok.sh
sudo ./setup_ngrok.sh $SSDPATH
##############################################################

# 9. Create directories for logs and images
mkdir -p $SSDPATH/trainspotting/logs/daily_aggregate
mkdir -p $SSDPATH/trainspotting/logs/train_detects
mkdir -p $SSDPATH/trainspotting/logs/train_images
mkdir -p $SSDPATH/trainspotting/images
mkdir -p $SSDPATH/trainspotting/service_logs
#############################################################

# 10. Enable all services for auto start on boot
sudo systemctl enable weewx
sudo systemctl enable run_camera.service
sudo systemctl enable run_purple_air.service
sudo systemctl enable run_ngrok.service
##############################################################

echo "Done setup. Please check logs/output for any errors/mishaps."

