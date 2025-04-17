# 1. git pull
cd /home/trainspotting/Trainspotting
git fetch
git checkout simplify

# 2. stop *all services
chmod u+x tools/stop_all.sh
./tools/stop_all.sh

# 3. add kernel config
cp setup/60-kernel.conf /etc/sysctl.d/60-kernel.conf

# 4. update camera scripts
rm /home/trainspotting/scripts/run_camera.py
rm /home/trainspotting/scripts/camera_utils/train_logger.py
rm /home/trainspotting/scripts/config/camera_config.py
rm /etc/systemd/system/run_camera.service
cp scripts/run_camera.py /home/trainspotting/scripts
cp scripts/camera_utils/train_logger.py /home/trainspotting/Trainspotting/scripts/camera_utils
cp scripts/config/camera_config.py /home/trainspotting/scripts/config
cp scripts/clear_camera_cache.sh /home/trainspotting/scripts
cp services/run_camera.service /etc/systemd/system

SSDPATH=(`sudo lsblk -o MOUNTPOINT | grep /media*`)
CAMERACONF="/home/trainspotting/scripts/config/camera_config.py"
search="default_output_path="
replace="default_output_path='${SSDPATH}/trainspotting/images/'\n# default_output_path="
sudo sed -i "s~${search}~${replace}~g" $CAMERACONF

# 5. add train_images_simple table to mysql
systemctl start mysql
mysql -u johndoe -ppassword < "fix.sql"
systemctl stop mysql

#6 update ngrok config
rm /home/trainspotting/scripts/config/ngrok_config.yml
cp scripts/config/ngrok_config.yml /home/trainspotting/scripts/config

# 7. Enable all and reboot
systemctl daemon-reload
systemctl enable mysql
systemctl enable run_camera
systemctl enable run_purple_air
systemctl enable mysql
systemctl enable run_weewx
systemctl enable run_ngrok
systemctl reboot
