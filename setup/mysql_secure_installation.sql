UPDATE mysql.user SET authentication_string=PASSWORD('root') WHERE User='root';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;

CREATE USER 'dhawal'@'localhost' IDENTIFIED BY 'april+1Hitmonlee';
GRANT ALL PRIVILEGES ON *.* TO 'dhawal'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;