#!/bin/bash

# script for setting up purple air to run on startup

#make sure serial is installed
apt-get install python3-serial -Vy

#make sure all service files are in the right folder
cp ./purple_air.service /etc/systemd/system/purple_air.service

#refreshes daemon list
systemctl daemon-reload

#enables the purple_air service to start on boot
systemctl enable purple_air

#use this command to disable the script  
# systemctl disable purple_air

