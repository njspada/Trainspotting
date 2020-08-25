#!/bin/bash
sudo systemctl stop run_trainspotting
R CMD BATCH --no-restore run_reporting.R
sudo systemctl enable run_trainspotting
sudo systemctl start run_trainspotting
sudo systemctl reboot