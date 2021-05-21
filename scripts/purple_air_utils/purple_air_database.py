import mysql.connector
import sys
from mysql.connector import errorcode

#cnx.close()

def write_to_db(timestamp, dataline, database_config):
    # timestamp must be "Y-m-d H:i:s"
    cnx = database_config.connection()
    values = dataline.split(',')
    values.insert(0, timestamp)
    
    #query = """INSERT INTO purple_air  
    #        (`dateTime`,`p03_avg`,`p03_sd`,`p10_avg`,`p10_sd`,
    #        `p25_avg,`p25_sd,`p50_avg`,`p50_sd`,`p100_avg`,
    #        `p100_sd`,`pm25_avg`,`pm25_sd`)
    #        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    query = """INSERT INTO purple_air
            (`datetime`,
	    `p03_A`,`p03_B`,`p03_C`,
	    `p05_A`,`p05_B`,`p05_C`,
	    `p10_A`,`p10_B`,`p10_C`,
	    `p25_A`,`p25_B`,`p25_C`,
	    `p50_A`,`p50_B`,`p50_C`,
	    `p100_A`,`p100_B`,`p100_C`,
	    `pm25_A`,`pm25_B`,`pm25_C`)
	    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,
	    %s,%s,%s,%s,%s,%s,%s,%s,
	    %s,%s,%s,%s,%s,%s);"""
    try:
      cursor = cnx.cursor()
      cursor.execute(query, values)
    except mysql.connector.Error as err:
      print(err)
    else:
      cnx.commit()

def get_latest_data(database_config):
    cnx = database_config.connection()
    query = """SELECT * 
                FROM purple_air
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
