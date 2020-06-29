import mysql.connector
import sys
from mysql.connector import errorcode

#print(len(sys.argv))

table = sys.argv[1]
user = sys.argv[2]
password = sys.argv[3]
database = sys.argv[4]

try:
    cnx = mysql.connector.connect(user=user, password=password, host='127.0.0.1', database=database)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("wrong user name or password!")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("db does not exist")
    else:
        print(err)
        print('hi')
else:
    cnx.close()



