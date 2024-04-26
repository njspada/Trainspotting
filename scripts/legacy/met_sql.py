import database_config
import mysql.connector
import sys
from mysql.connector import errorcode

def get_latest_data():
    cnx = database_config.connection(database='weewx')
    query = """SELECT * 
                FROM archive
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

