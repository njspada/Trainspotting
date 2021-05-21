NGROKHOST=$(curl -s http://35.162.211.43/get_ngrok_host.php)
DEVICEID=$1
if [ $NGROKHOST -eq $DEVICEID ]
	then sudo systemctl start run_ngrok && echo "starting ngrok"
       	else sudo systemctl stop run_ngrok && echo "stopping ngrok"
fi
