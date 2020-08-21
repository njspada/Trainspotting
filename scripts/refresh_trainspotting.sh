sudo systemctl stop run_trainspotting
R CMD BATCH --no-restore run_reporting.R
sudo systemctl reboot