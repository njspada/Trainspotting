#!/bin/bash
# 1. Utils
sudo apt-get install -yq libpython3-dev
##############################################################

# 2. Edgetpu reqs from https://www.pyimagesearch.com/2019/04/22/getting-started-with-google-corals-tpu-usb-accelerator/
sudo echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
sudo curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install -yq libedgetpu1-std
sudo apt-get install -yq python3-edgetpu
# wget https://bootstrap.pypa.io/get-pip.py
# sudo python get-pip.py
# sudo python3 get-pip.py
# sudo rm -rf ~/.cache/pip
# no need to install a virtual env for now
sudo -H pip3 install numpy
sudo -H pip3 install opencv-contrib-python==4.1.0.25
sudo -H pip3 install imutils
sudo -H pip3 install pillow
sudo -H pip3 install scipy
sudo apt-get install -yq edgetpu-examples
sudo chmod a+w /usr/share/edgetpu/examples
# models and label files stored in /usr/share/edgetpu/examples/models
##############################################################

# 3. Configure ssd location
CAMERACONF="/home/trainspotting/Trainspotting/scripts/config/camera_config.py"
search="default_output_path="
replace="default_output_path=${SSDPATH}/trainspotting/images/\n# default_output_path="
sudo sed -i 's~${search}~${replace}~g' $CAMERACONF
##############################################################

# 4. Install MySQL for Python3
sudo -H pip3 install mysql-connector-python
##############################################################

# 5. Setup systemd service
sudo cp /home/trainspotting/Trainspotting/services/run_camera.service /etc/system/systemd
sudo chmod +x /etc/systemd/system/run_camera.service
##############################################################
