import mysql.connector
import sys
from mysql.connector import errorcode

#print(len(sys.argv))

def connection(database='trainspotting'):
    user = 'dhawal'
    password = 'april+1Hitmonlee'
    #database = 'trainspotting'

    try:
        cnx = mysql.connector.connect(user=user, password=password, host='127.0.0.1', database=database)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("wrong user name or password!")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("db does not exist")
        else:
            print(err)
    else:
        return cnx



