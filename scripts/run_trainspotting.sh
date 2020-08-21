#!/bin/bash
python3 run_camera.py &
sudo python3 run_purple_air.py &
sudo /etc/init.d/weewx start &
sudo ./home/coal/Desktop/cloud/ngrok tcp 22 &
wait