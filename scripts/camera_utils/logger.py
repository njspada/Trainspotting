import mysql.connector
from mysql.connector import errorcode
from os import makedirs
from PIL import Image
from datetime import datetime

def run_insert_query(query, data, config):
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

def save_frame(image,args,cnx):
    # print('1')
    t = datetime.now()
    date = t.strftime('%Y-%m-%d')
    hour = t.strftime('%H')
    stamp = int(t.timestamp())
    filepath = f"{args.outputpath}{date}/{hour}/"
    filename = f"{stamp}.jpg"
    # print('2')
    try:
        makedirs(filepath)
        # print('3')
    except:
        # print('4')
        print('Error with makedir!')
    try:
        # print('5')
        Image.fromarray(image).save(f"{filepath}{filename}")
    except:
        # print('6')
        print('pillow image error')
    query = """INSERT INTO train_images
            (filename, dateTime)
            VALUES (%s,%s);
    """
    _ = run_insert_query(query, [f"{filepath}/{filename}", stamp], cnx)
