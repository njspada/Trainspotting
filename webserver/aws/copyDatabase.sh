#!/bin/bash
chmod 400 nickKey_Oregon.pem
scp -i nickKey_Oregon.pem bitnami@100.22.13.192:/home/bitnami/trainspotting.sql .