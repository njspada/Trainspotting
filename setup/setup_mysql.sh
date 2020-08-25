#!/bin/bash

# 1. Install MySQL package
sudo apt update
sudo apt-get install -yq mysql-server
##############################################################

# 2. Custom run for `mysql_secure_installation`.
#    This will set root's password to `root` and create new user "dhawal".
mysql -sfu root < "mysql_secure_installation.sql"
##############################################################

# 3. Create trainspotting database and tables from template file.
mysql -u dhawal -p april+1Hitmonlee < "field_database_template.sql"
##############################################################

# 3. Move MySQL data directory to ssd
sudo systemctl stop mysql
sudo cp -r /var/lib/mysql "${SSDPATH}/trainspotting"
sudo mv /var/lib/mysql /var/lib/mysql.bak
##############################################################

# 4. Update MySQL config with new datadir location
MYSQLCONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
search="datadir="
replace="data=${SSDPATH}/trainspotting/mysql\n# datadir="
sudo sed -i 's~${search}~${replace}~g' $MYSQLCONF
##############################################################

# 4. update apparmor with new location
echo "alias /var/lib/mysql/ -> ${SSDPATH}/trainspotting/mysql/," >> /etc/apparmor.d/tunables/alias
sudo systemctl restart apparmor
##############################################################

# 5. create empty dir to silence mysql error
sudo mkdir /var/lib/mysql/mysql -p
sudo systemctl enable mysql
sudo systemctl start mysql
##############################################################
