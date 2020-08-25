#!/bin/bash
# 1. stop all scripts/services
sudo systemctl stop run_camera.service
sudo systemctl stop run_purple_air.service
sudo systemctl stop weewx
##############################################################

# 2. run reporting R script
Rscript /home/trainspotting/Trainspotting/scripts/run_reporting.R
##############################################################

# 3. git pull
cd /home/trainspotting/Trainspotting
git pull
if[-z "ls update.sh"]
then
	echo "No updates. Restarting services and rebooting."
else
	echo "Running update script."
	sudo chmod u+x update.sh
	sudo ./update.sh

# 4. 