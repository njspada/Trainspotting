#!/bin/bash
# 1. Utils
sudo apt-get install libpython3-dev
##############################################################

# 2. Edgetpu reqs from https://www.pyimagesearch.com/2019/04/22/getting-started-with-google-corals-tpu-usb-accelerator/
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install libedgetpu1-std
sudo apt-get install python3-edgetpu
# wget https://bootstrap.pypa.io/get-pip.py
# sudo python get-pip.py
# sudo python3 get-pip.py
# sudo rm -rf ~/.cache/pip
# no need to install a virtual env for now
sudo pip3 install numpy
sudo pip3 install opencv-contrib-python==4.1.0.25
sudo pip3 install imutils
sudo pip3 install pillow
sudo pip3 install scipy
sudo apt-get install edgetpu-examples
sudo chmod a+w /usr/share/edgetpu/examples
# models and label files stored in /usr/share/edgetpu/examples/models
##############################################################

# 3. Configure ssd location
CAMERACONF="/home/trainspotting/Trainspotting/scripts/config/camera_config.py"
mv "$CAMERACONF" "$CAMERACONF.bak"
cat "$CAMERACONF.bak" | grep -v "^default_output_path=" > "$CAMERACONF"
echo "default_output_path=${SSDPATH}/trainspotting/images" >> "$CAMERACONF"
##############################################################

# 4. Install MySQL for Python3
pip3 install mysql-connector-python
##############################################################

# 5. Setup systemd service
sudo cp /home/trainspotting/Trainspotting/services/run_camera.service /etc/system/systemd
sudo chmod +x /etc/system/systemd/run_camera.service
##############################################################