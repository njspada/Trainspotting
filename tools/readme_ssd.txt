This file describes the steps to setup a new SSD for the system.

Ref link - https://www.linux.org/threads/comparison-of-file-systems-for-an-ssd.28780/

- Desired filesystem is ext4 because: 1. No required packages to install. 2. Really fast access.

sudo mkfs ext4 -L ssd_T5 /dev/sd#

- Replace # with correct char from `lsblk`. 
