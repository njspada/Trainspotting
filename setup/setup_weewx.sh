#!/bin/bash

# 1. install reqs
sudo apt update
sudo apt install -yq python3-configobj
sudo apt install -yq python3-pil
sudo apt install -yq python3-serial
sudo apt install -yq python3-usb
sudo -H /usr/bin/python3 -m pip install Cheetah3
sudo apt install -yq python3-mysqldb
##############################################################

# 2. download archive, unzip, run setup
cd /home/trainspotting
sudo curl http://weewx.com/downloads/released_versions/weewx-4.1.1.tar.gz -o weewx_archive.tgz
sudo tar -xvzf weewx_archive.tgz
cd weewx-*
sudo python3 ./setup.py build
sudo python3 ./setup.py install --no-prompt
##############################################################

# 3. replace default configuration with backup
sudo rm /home/weewx/weewx.conf
sudo cp /home/trainspotting/scripts/config/weewx.conf /home/weewx
##############################################################

# 4. update device usb location
DRIVER="cp210x"
WEATHER_DEVICE_NAME="vantage-usb"
echo "DRIVERS==\"${DRIVER}\",SYMLINK+=\"${WEATHER_DEVICE_NAME}\"" >> /etc/udev/rules.d/99-usb-serial.rules
udevadm trigger
echo "WEATHER_DEVICE_NAME=${WEATHER_DEVICE_NAME}" >> /home/trainspotting/info.txt

# LOC=$(ls /sys/bus/usb/drivers/cp210x/1-*/tty*/tty)
LOC="${WEATHER_DEVICE_NAME}"
WEEWXCONF="/home/weewx/weewx.conf"
search="port ="
replace="port = /dev/${LOC}\n# port ="
sed -i "s~${search}~${replace}~g" $WEEWXCONF
##############################################################

# 4. set archive interval
sudo /home/weewx/bin/wee_device --set-interval=1
##############################################################

#4. Setup systemd service
cd /home/trainspotting/services
sudo cp run_weewx.service /etc/systemd/system
# sudo chmod u+x /etc/systemd/system/run_weewx.service
##############################################################
