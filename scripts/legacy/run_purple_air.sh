#! /bin/sh

# running the purple air script
logger "Starting Purple Air Script"
for i in 'seq 1 50';
do
	logger 'Trying to Connect to Purple Air'
        #set program arguments here     
	python3 /usr/local/controller/tools/purple_air.py --path /usr/local/output
	logger 'Connection to Purple Air Interupted'
	sleep 40
done


