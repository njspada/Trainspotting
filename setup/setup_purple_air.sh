#!/bin/bash

# 1. Install reqs
sudo apt-get install -yq python3-serial
sudo -H pip3 install argparse
##############################################################

# 2. Setup systemd service
sudo cp /home/trainspotting/services/run_purple_air.service /etc/systemd/system
# sudo chmod u+x /etc/systemd/system/run_purple_air.service
##############################################################

# 3. update device usb location
# DRIVER="ch341"
#PRODUCT="Ruggeduino"
PRODUCT="Arduino Nano Every"
PA_DEVICE_NAME="purple-air-usb"
# echo "DRIVERS==\"${DRIVER}\",SYMLINK+=\"${PA_DEVICE_NAME}\"" >> /etc/udev/rules.d/99-usb-serial.rules
echo "SUBSYSTEM==\"usb\"ATTR{product}==\"${PRODUCT}\",SYMLINK+=\"${PA_DEVICE_NAME}\"" >> /etc/udev/rules.d/99-usb-serial.rules
udevadm trigger
echo "WEATHER_DEVICE_NAME=${PA_DEVICE_NAME}" >> /home/trainspotting/info.txt

# LOC=$(ls /sys/bus/usb/drivers/cp210x/1-*/tty*/tty)
# LOC="${WEATHER_DEVICE_NAME}"
# WEEWXCONF="/home/weewx/weewx.conf"
# search="port ="
# replace="port = /dev/${LOC}\n# port ="
# sed -i "s~${search}~${replace}~g" $WEEWXCONF
##############################################################
