import mysql.connector
import sys
from mysql.connector import errorcode

def write_to_db(timestamp, dataline, database_config):
    # timestamp must be "Y-m-d H:i:s"
    cnx = database_config.connection()

    values = dataline.split(',')
    values.insert(0, timestamp)

    query = """INSERT INTO rugged_air (dateTime,
            pm25_a, pm25_b, pm25_c) 
            VALUES (%s, %s, %s, %s)"""

    query2 = query%tuple(values)

    try:
        cursor = cnx.cursor()
        cursor.execute(query2)
    except mysql.connector.Error as err:
        print(err)
    else:
        cnx.commit()

def get_latest_data(database_config):
    cnx = database_config.connection()
    query = """SELECT * 
                FROM rugged_air
                ORDER BY datetime DESC
                LIMIT 1""";
    try:
        cursor = cnx.cursor()
        cursor.execute(query)
    except mysql.connector.Error as err:
        print(err)
    else:
        row = dict(zip(cursor.column_names, cursor.fetchone()))
        return row