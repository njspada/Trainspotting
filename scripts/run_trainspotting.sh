#!/bin/bash
python3 run_camera.py &
sudo python3 run_purple_air.py &
sudo /etc/init.d/weewx start &
sudo systemctl start ngrok.service
sudo systemctl enable ngrok.service
wait