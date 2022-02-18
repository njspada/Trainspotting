#!/bin/bash
# Before running setup do this:
#	- unplug coral usb
#	- plug in purple air usb
#	- plug in weewx usb
#	- plug in ssd usb
#	- reboot
# 	- sudo mkdir /home/trainspotting
# 	- cd /home/trainspotting
# 	- sudo vi setup_device.sh (and paste this file in)
# 	- sudo chmod +x setup_device.sh
# 	- sudo ./setup_device.sh 2>&1 | tee /home/coal/output.txt

# 0. add excludes
# ./setup_device [service]
# service = to be excluded
# supports - weewx, purple_air, reporting
setup_weewx=1
setup_purple_air=1
setup_reporting=1
for service in "$@"
do
	case "${service}" in
		weewx) setup_weewx=0;;
		purple_air) setup_purple_air=0;;
		reporting) setup_reporting=0;;
	esac
done

# 1. upgrade system.install python3, pip3, curl
sudo apt-get update
sudo apt-get upgrade -yq
sudo apt-get install -yq curl
sudo apt-get install -yq python3-pip
sudo apt-get install dos2unix
##############################################################

# 2. set noninteractive frontend, AWSURL, [device]INFO
export DEBIAN_FRONTEND=noninteractive
AWSURL="http://100.22.13.192/"
INFO="/home/trainspotting/info.txt"
echo "AWSURL=${AWSURL}" >> $INFO
echo "AWSURL=${AWSURL}" >> /etc/environment
##############################################################

# 3. Set device name and report_time.
echo "Printing device names and report times:"
# curl -s http://54.188.2.207/get_report_times.php | cat
curl -s ${AWSURL}get_report_times.php | cat
echo -n "Enter a device name: "
read DEVICE_NAME
echo -n "Enter a device report time (MM HH): "
read REPORT_TIME
EREPORT_TIME=$(echo $REPORT_TIME | sed 's/ /%20/g')
# url="http://54.188.2.207/setup_device.php?name=$DEVICE_NAME&report_time=$EREPORT_TIME"
url="${AWSURL}/setup_device.php?name=$DEVICE_NAME&report_time=$EREPORT_TIME"
echo $url
response=$(curl -i -s $url)
DEVICE_ID=${response##*=}
DEVICE_ID=${DEVICE_ID%%;*}
FS="Failed to setup device.\nPrinting response and exiting."
SS="Successfully setup device. Device id=$DEVICE_ID."
if [[ -z $( echo "$response" | grep "200 OK" ) ]]; then echo 'Failed'; exit; else echo "$SS"; fi
echo "DEVICE_ID=${DEVICE_ID}" >> $INFO
echo "DEVICE_NAME=${DEVICE_NAME}" >> $INFO
echo "REPORT_TIME=${REPORT_TIME}" >> $INFO
# echo "DEVICE_ID=${DEVICE_ID}" >> ~/.profile
# echo "DEVICE_NAME=${DEVICE_NAME}" >> ~/.profile
# echo "REPORT_TIME=${REPORT_TIME}" >> ~/.profile
echo "DEVICE_ID=${DEVICE_ID}" >> /etc/environment
echo "DEVICE_NAME=${DEVICE_NAME}" >> /etc/environment
echo "REPORT_TIME=${REPORT_TIME}" >> /etc/environment
##############################################################

# 4. git clone from production branch and copy project directories out of git directory
sudo mkdir /home/trainspotting
cd /home/trainspotting
#sudo git clone --depth=1 --single-branch --branch simplify https://dmmajithia:3e4eda1c57ad3c97950c9fb2e02da56a1110b0dc@github.com/njspada/Trainspotting.git
sudo cp -rp Trainspotting/scripts /home/trainspotting
sudo cp -rp Trainspotting/setup /home/trainspotting
sudo cp -rp Trainspotting/services /home/trainspotting
##############################################################

# 5. Find external ssd path and mount unit name
SSDPATH=(`sudo lsblk -o MOUNTPOINT | grep /media*`)
MOUNTUNIT=(`systemctl list-units --type=mount | grep ${SSDPATH}`)
MOUNTUNIT=$(echo ${MOUNTUNIT} | sed --expression="s/-/\x2d/g")
echo "SSDPATH=${SSDPATH}" >> $INFO
echo "MOUNTUNIT=${MOUNTUNIT}" >> $INFO
# echo "SSDPATH=${SSDPATH}" >> ~/.profile
# echo "MOUNTUNIT=${MOUNTUNIT}" >> ~/.profile
echo "SSDPATH=${SSDPATH}" >> /etc/environment
echo "MOUNTUNIT=${MOUNTUNIT}" >> /etc/environment
sudo mkdir ${SSDPATH}/trainspotting
##############################################################

# 6. Setup MySQL
cd /home/trainspotting/setup
dos2unix setup_mysql.sh
sudo chmod u+x setup_mysql.sh
sudo ./setup_mysql.sh $SSDPATH $MOUNTUNIT
##############################################################

# 7. Setup WeeWX
if [ $setup_weewx -eq 0 ];then
	echo "Skipping WeeWX setup"
else
	cd /home/trainspotting/setup
	dos2unix setup_weewx.sh
	sudo chmod u+x setup_weewx.sh
	sudo ./setup_weewx.sh
fi
##############################################################

# 8. Setup utils for run_camera
cd /home/trainspotting/setup
dos2unix setup_camera.sh
sudo chmod u+x setup_camera.sh
sudo ./setup_camera.sh $SSDPATH
##############################################################

# 9. Setup utils for run_purple_air
if [ $setup_purple_air -eq 0 ]
	then echo "Skipping Purple Air setup"
else
	cd /home/trainspotting/setup
	dos2unix setup_purple_air.sh
	sudo chmod u+x setup_purple_air.sh
	sudo ./setup_purple_air.sh
fi
##############################################################

# 10. Setup utils for run_reporting
if [ $setup_reporting -eq 0 ]
	then echo "Skipping Reporting setup"
else
	cd /home/trainspotting/setup
	dos2unix setup_reporting.sh
	sudo chmod u+x setup_reporting.sh
	sudo ./setup_reporting.sh $SSDPATH $DEVICE_ID $DEVICE_NAME $REPORT_TIME
fi
##############################################################

# 11. Setup Ngrok
cd /home/trainspotting/setup
dos2unix setup_ngrok.sh
sudo chmod u+x setup_ngrok.sh
sudo ./setup_ngrok.sh $SSDPATH
##############################################################

# 12. Setup status checker
cd /home/trainspotting/services
STATCHECKER="/home/trainspotting/services/status_checker2"
SERVICE="/home/trainspotting/services/run_status_checker.service"
search="ssd-path-here"
replace="${SSDPATH}"
sed -i "s~${search}~${replace}~g" $STATCHECKER
sed -i "s~${search}~${replace}~g" $SERVICE
search="device-id-here"
replace="${DEVICE_ID}"
sed -i "s~${search}~${replace}~g" $SERVICE
sudo chmod u+x status_checker2
sudo cp $SERVICE /etc/systemd/system
sudo crontab -l > tabs
echo "*/15 * * * * systemctl start run_status_checker" >> tabs
# echo "00 * * * * ${STATCHECKER} ${DEVICE_ID} >> ${SSDPATH}/trainspotting/service_logs/status_checker.log 2>&1" >> tabs
# echo "@reboot root sleep 60 && ${STATCHECKER} ${DEVICE_ID} >> ${SSDPATH}/trainspotting/service_logs/status_checker.log 2>&1" >> tabs
sudo crontab tabs
sudo rm tabs
##############################################################

# 13. Create directories for logs and images on SSD
mkdir -p $SSDPATH/trainspotting/logs/daily_aggregate
mkdir -p $SSDPATH/trainspotting/logs/train_detects
mkdir -p $SSDPATH/trainspotting/logs/train_images
mkdir -p $SSDPATH/trainspotting/images
mkdir -p $SSDPATH/trainspotting/service_logs
#############################################################

# 14. Enable all services for auto start on boot
sudo systemctl daemon-reload
sudo systemctl enable mysql
sudo systemctl enable run_weewx.service
sudo systemctl enable run_camera.service
sudo systemctl enable run_purple_air.service
sudo systemctl enable run_ngrok.service
sudo systemctl enable run_status_checker.service
##############################################################

# 15. Clean up
cd /home/trainspotting
sudo rm -rf ngrok_archive.zip weewx*
# delete logs at 5am everyweek on monday
sudo crontab -l > tabs
echo "0 5 * * 1 rm /var/log/*" >> tabs
sudo crontab tabs
sudo rm tabs
# sudo ./home/trainspotting/services/status_checker ${DEVICE_ID} >> ${SSDPATH}/trainspotting/service_logs/status_checker.log 2>&1
##############################################################

echo "Done setup. Please check logs/output for any errors/mishaps."