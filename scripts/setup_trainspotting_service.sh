#!/bin/bash
cp run_trainspotting.service /etc/systemd/system
chmod u+x run_trainspotting.sh

cp run_ngrok.service /etc/systemd/system

systemctl daemon-reload