#!/bin/bash

# 1. Install reqs
sudo apt-get install python3-serial
sudo pip3 install argparse
##############################################################

# 2. Setup systemd service
sudo cp /home/trainspotting/Trainspotting/services/run_purple_air.service /etc/system/systemd
sudo chmod u+x /etc/systemd/system/run_purple_air.service
##############################################################