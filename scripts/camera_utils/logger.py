import mysql.connector
from mysql.connector import errorcode
from os import makedirs
from PIL import Image
from datetime import datetime

def run_insert_query(query, data, cnx):
    try:
        cursor = cnx.cursor()
        cursor.execute(query, data)
    except mysql.connector.Error as err:
        print(err)
        return -1
    cnx.commit()
    return cursor.lastrowid

def save_frame(image,args,cnx):
    if not cnx:
        return
    t = datetime.now()
    date = t.strftime('%Y-%m-%d')
    hour = t.strftime('%H')
    stamp = int(t.timestamp())
    filepath = f"{args.outputpath}{date}/{hour}/"
    filename = f"{stamp}.jpg"
    try:
        makedirs(filepath)
    except:
        self.print('Error with makedir!')
    Image.fromarray(image).save(f"{filepath}/{filename}")
    query = """INSERT INTO train_images
            (filename, dateTime)
            VALUES (%s,%s);
    """
    _ = run_insert_query(query, [f"{filepath}/{filename}", stamp], cnx)