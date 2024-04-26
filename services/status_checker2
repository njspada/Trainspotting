#!/bin/bash

DSTR=$(date +%s)
DEVICE_ID=$1
logfile="/media/jetsonssd/trainspotting/service_logs/ngrok.log"
CNXN=$(grep "started tunnel" ${logfile} | tail -1 | rev | cut -d'=' -f 1 | cut -d'/' -f 1 | rev)
URL=$(echo $CNXN | cut -d':' -f 1)
PRT=$(echo $CNXN | cut -d':' -f 2)


post_url="${AWSURL}new_status_update.php"

services=('mysql' 'run_weewx' 'run_ngrok' 'run_camera' 'run_purple_air' 'nvargus-daemon')
processes=('mysql' 'weewx' 'ngrok' 'run_camera' 'run_purple_air' 'nvargus-daemon')

ps -o %mem,command ax > tmpmem
tmpjson="{"

arraylength=${#processes[@]}

# use for loop to read all values and indexes
for (( i=0; i<${arraylength}; i++ ));
do
	s=${services[$i]}
	p=${processes[$i]}
	mempercent=$(cat tmpmem | grep ${p} | cut -d ' ' -f2)
	substate=$(systemctl show -p SubState $s | cut -d= -f2)
	# echo "${s}:${substate},${s}_mem:${mempercent}," >> tmpjson
	tmpjson="${tmpjson}${s}:\"${substate}\",${s}_mem:\"${mempercent}\","
done
rm tmpmem
# echo "device_id:${DEVICE_ID},dateTime:dateTime=${DSTR}}" >> tmpjson
tmpjson="${tmpjson}device_id:\"${DEVICE_ID}\",dateTime:\"${DSTR}\",url:\"${URL} -p ${PRT}\"}"
tmpjson=$(echo $tmpjson | sed -e "s/-/_/g")
json=$(jq -n "$tmpjson")
echo $json >> tmpjson
# echo $tmpjson

# if [ -z $DEVICE_ID ]; then exit; fi

curl -s -X POST -H "Content-Type: application/json" -d @tmpjson $post_url
rm tmpjson