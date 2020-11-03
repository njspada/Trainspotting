import mysql.connector
from mysql.connector import errorcode
from os import makedirs
from PIL import Image
from datetime import datetime
from collections import deque
from enum import Enum, auto

class LoggerState(Enum):
    train_event_on = auto()
    train_event_off = auto()
    stationary = auto()

class Logger:

    def __init__(self, db_config, ARGS):
        self.ARGS = ARGS
        self.db_config = db_config
        self.classify_history_deque = deque(maxlen=ARGS.len_classify_history_deque)
        self.classify_history_sum = 0
        self.state = LoggerState.train_event_off

    def G(self, is_train_p):
        '''
            This is the activation function for a LoggerState transitions.
            Input: X.is_train_p: value between 0.0-1.0 - from the main camera script.
            Output: Destination LoggerState
        '''
        if self.classify_history_deque.count() > 0:
            d = self.classify_history_deque.popleft()
            self.classify_history_sum -= d
        self.classify_history_deque.append(is_train_p)
        self.classify_history_sum += is_train_p
        classify_history_p_avg = self.classify_history_sum / self.classify_history_deque.count()

        if classify_history_p >= self.ARGS.classify_history_p_threshold:
            if time.time() <= self.train_event_start_time + self.ARGS.max_train_event_time:
                return LoggerState.train_event_on

            else:
                return LoggerState.stationary
        else:
            return LoggerState.train_event_off

    def ChangeState(self, dest_state):
        if self.state == LoggerState.train_event_on and dest_state != LoggerState.train_event_on:
            self.event_id = -1
        elif self.state == LoggerState.stationary and dest_state == LoggerState.train_event_off:
            self.event_id = -1
        self.state = dest_state

    def Input(self, X):
        '''
            This is the main logger input function for a camera frame.
            Input: X - from the main camera script.
                    Dictionary: {img: Numpy array,
                                 is_train_p: [0.0-1.0]}
            Output: None.
        '''
        dest_state = self.G(X.is_train_p)
        self.ChangeState(dest_state)
        


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
        Image.fromarray(image).save(f"{filepath}/{filename}")
    except:
        # print('6')
        print('pillow image error')
    query = """INSERT INTO train_images_simple
            (filename, dateTime)
            VALUES (%s,%s);
    """
    _ = run_insert_query(query, [f"{filepath}/{filename}", stamp], cnx)