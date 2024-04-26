import mysql.connector
import sys
from mysql.connector import errorcode
from config import local_database_config as ARGS

#print(len(sys.argv))

def connection(database='trainspotting'):
    try:
        cnx = mysql.connector.connect(user=ARGS.user, password=ARGS.password, host=ARGS.host, database=database)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("wrong user name or password!")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("db does not exist")
        else:
            print(err)
    else:
        return cnx



