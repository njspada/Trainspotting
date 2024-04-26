#!/bin/bash

SSDPATH=$1
MOUNTUNIT=$2

# 1. Install MySQL package
sudo apt update
sudo apt-get install -yq mysql-server
##############################################################

# 2. Custom run for `mysql_secure_installation`.
#    This will set root's password to `root` and create new user "dhawal".
sudo mysql -sf < "mysql_secure_installation.sql"
##############################################################

# 3. Create trainspotting database and tables from template file.
mysql -u dhawal -papril+1Hitmonlee < "field_database_template.sql"
##############################################################

# 3. Move MySQL data directory to ssd
sudo systemctl stop mysql
sudo cp -rp /var/lib/mysql "${SSDPATH}/trainspotting/mysql"
sudo mv /var/lib/mysql /var/lib/mysql.bak
##############################################################

# 4. Update MySQL config with new datadir location
MYSQLCONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
search="datadir"
replace="datadir=${SSDPATH}/trainspotting/mysql\n# datadir="
sudo sed -i "s~${search}~${replace}~g" $MYSQLCONF
##############################################################

# 4. Update apparmor with new location
echo "alias /var/lib/mysql/ -> ${SSDPATH}/trainspotting/mysql/," >> /etc/apparmor.d/tunables/alias
sudo systemctl restart apparmor
##############################################################

# 5. Create empty dir to silence mysql data dir not found error
sudo mkdir /var/lib/mysql/mysql -p
##############################################################

# 6. Add ssd path and mount unit to mysql systemd service file.
# Then reenable mysql service with this custom service file
MYSQLSERVICE="/home/trainspotting/services/mysql.service"
search="ssd-path-here"
sudo sed -i "s~${search}~${SSDPATH}~g" $MYSQLSERVICE
search="mount-unit-here"
sudo sed -i "s~${search}~${MOUNTUNIT}~g" $MYSQLSERVICE
sudo cp /home/trainspotting/services/mysql.service /etc/systemd/system
sudo systemctl reenable mysql.service
##############################################################