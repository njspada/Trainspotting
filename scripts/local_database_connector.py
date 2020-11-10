import mysql.connector
import sys
from mysql.connector import errorcode
from config import local_database_config as ARGS
from tthreading import threaded

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

@threaded
def ExecuteQuery(query, data):
    try:
        # print('7')
        cnx = config.connection()
        # print('8')
        cursor = cnx.cursor()
        # print('9')
        cursor.execute(query, data)
        # print('10')
        cnx.commit()
        # print('11')
        return cursor.lastrowid
    except mysql.connector.Error as err:
        # print('1')
        print(err)
        return -1

