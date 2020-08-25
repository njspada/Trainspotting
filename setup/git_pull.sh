#!/bin/bash

# 1. git pull production branch
git clone --single-branch --branch production https://dmmajithia:3e4eda1c57ad3c97950c9fb2e02da56a1110b0dc@github.com/njspada/Trainspotting.git

# 2. cd into `Trainspotting/setup`
./setup_device.sh