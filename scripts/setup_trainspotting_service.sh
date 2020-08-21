cp run_trainspotting.service /etc/systemd/system
chmod u+x run_trainspotting.sh
systemctl enable run_trainspotting
systemctl start run_trainspotting