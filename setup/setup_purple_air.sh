#!/bin/bash

# 1. Install reqs
sudo apt-get install -yq python3-serial
sudo -H pip3 install argparse
##############################################################

# 2. Setup systemd service
sudo cp /home/trainspotting/Trainspotting/services/run_purple_air.service /etc/systemd/system
# sudo chmod u+x /etc/systemd/system/run_purple_air.service
##############################################################
