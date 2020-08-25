#!/bin/bash

# 1. install reqs
sudo apt update
sudo apt install python3-configobj
sudo apt install python3-pil
sudo apt install python3-serial
sudo apt install python3-usb
sudo /usr/bin/python3 -m pip install Cheetah3
sudo apt install python3-mysqldb
##############################################################

# 2. download archive, unzip, run setup
sudo cd /home/trainspotting
sudo curl http://weewx.com/downloads/weewx-4.1.1.tar.gz -o weewx_archive.tgz
sudo tar -xvzf weewx_archive.tgz
sudo cd weewx-*
sudo python3 ./setup.py build
sudo python3 ./setup.py install --no-prompt
##############################################################

# 3. replace default configuration with backup
sudo rm /home/weewx/weewx.conf
sudo cp /home/trainspotting/Trainspotting/scripts/config/weewx.conf /home/weewx
##############################################################

# 4. update device usb location
LOC=$(ls sys/bus/usb/drivers/cp210x/1-*/tty*/tty)
WEEWXCONF="/home/weewx/weewx.conf"
search="port ="
replace="port = /dev/${LOC}\n# port ="
sed -i "s~${search}~${replace}~g" $WEEWXCONF
##############################################################

# 4. set archive interval
sudo /home/weewx/bin/wee_device --set-interval=1
##############################################################

#4. enable daemon service
sudo cd /home/weewx
sudo cp util/init.d/weewx.debian /etc/init.d/weewx
sudo chmod +x /etc/init.d/weewx
sudo update-rc.d weewx defaults 98
sudo /etc/init.d/weewx start
##############################################################