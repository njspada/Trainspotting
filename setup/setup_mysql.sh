# 1. Install MySQL
sudo apt update
sudo apt-get install mysql-server
export DEBIAN_FRONTEND=noninteractive
mysql -sfu root < "mysql_secure_installation.sql"
mysql -u dhawal -p april+1Hitmonlee < "field_database_template.sql"
##############################################################

# 2. Move MySQL data directory to ssd
sudo systemctl stop mysql
# copy the datadir to new location
sudo cp -r /var/lib/mysql "${SSDPATH}/trainspotting"
sudo mv /var/lib/mysql /var/lib/mysql.bak

# update mysql config with new location
MYSQLCONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
mv "$MYSQLCONF" "$MYSQLCONF.bak"
cat "$MYSQLCONF.bak" | grep -v "^datadir=" > "$MYSQLCONF"
echo "data=${SSDPATH}/trainspotting/mysql" >> "$MYSQLCONF"

# update apparmor with new location
echo "alias /var/lib/mysql/ -> ${SSDPATH}/trainspotting/mysql/," >> /etc/apparmor.d/tunables/alias
sudo systemctl restart apparmor

# create empty dir to silence mysql error
sudo mkdir /var/lib/mysql/mysql -p
sudo systemctl start mysql