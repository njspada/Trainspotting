#!/bin/bash
echo "Will not stop/disable ngrok!"
sudo systemctl stop mysql
sudo systemctl stop run_weewx.service
sudo systemctl stop run_camera.service
sudo systemctl stop run_purple_air.service
sudo systemctl disable mysql
sudo systemctl disable run_weewx.service
sudo systemctl disable run_camera.service
sudo systemctl disable run_purple_air.service