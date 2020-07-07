import database_config
import mysql.connector
import sys
from mysql.connector import errorcode

cnx = database_config.connection()

s_names = ['datetime', 'pm2.5', 'pm1', 'pm10', 'p0.3', 'p0.5', 'p1', 'p2.5', 'p5', 'p10']
name_dict = {pair for pair in enumerate(s_names)}

if cnx:
    print('successfully connected to database')

#cnx.close()

def write_to_db(timestamp, dataline):
    # timestamp must be "Y-m-d H:i:s"
    cnx = database_config.connection()
    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    names = ['datetime', 'datetime2', 'mac', 'firmware', 'hardware',
                  'tempF', 'rh', 'dewptF', 'pres', 'adc', 'mem', 'rssi',
                  'uptime',
                  'pm1', 'pm2.5', 'pm10',
                  'pm1_cf', 'pm2.5_cf', 'pm10_cf', # V19
                  'junk1', 'junk2', # V21
                  'p0.3', 'p0.5', 'p1', 'p2.5', 'p5', 'p10', # V27
                  'pm1_b', 'pm2.5_b', 'pm10_b',
                  'pm1_cf_b', 'pm2.5_cf_b', 'pm10_cf_b', # V33
                  'junk3', 'junk4',
                  'p0.3_b', 'p0.5_b', 'p1_b', 'p2.5_b', 'p5_b', 'p10_b',
                  'junk5']
    values = dataline.split(',')
    values.insert(0, timestamp)
    pa = dict(zip(names,values))
    
    selected = [pa[s_name] for s_name in s_names]
    query = """INSERT INTO purple_air  
            (datetime, `pm2.5`, `pm1`, `pm10`, `p0.3`, `p0.5`, `p1`, `p2.5`, `p5`, `p10`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    try:
      cursor = cnx.cursor()
      cursor.execute(query, selected)
    except mysql.connector.Error as err:
      print(err)
    else:
      cnx.commit()

def get_latest_data():
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
