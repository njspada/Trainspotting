import mysql.connector
from mysql.connector import errorcode
from os import makedirs
from PIL import Image
from datetime import datetime
from collections import deque
from enum import Enum, auto
from tthreading import threaded
import local_database_connector as database

class LoggerState(Enum):
    train_event_on = 0
    train_event_off = 1
    stationary = 2

class LoggerInput:
    def __init__(self, image, is_train_p):
        self.image = image
        self.is_train_p = is_train_p
        self.t = datetime.now()

@threaded
def SaveImage(image,path,fullpathname):

    try:
        makedirs(path)
    except:
        print('Makedirs error.')
    try:
        image.save(fullpathname)
    except:
        print('PIL.Image error.')

@threaded
def SaveFrame(X,state,event_id,image_id,outputpath):

    # Insert records in 2 tables - train_detects & train_images
    train_detects_query = """INSERT INTO train_detects
    (event_id,type,image_id,label,score,x0,y0,x1,y1)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    train_detects_data = [event_id,state.value,image_id,
                          'train' if state.value==1 else 'no train',
                          int(X.is_train_p*100),
                          0,0,0,0]
    database.ExecuteQuery(train_detects_query, train_detects_data)

    date = X.t.strftime('%Y-%m-%d')
    hour = X.t.strftime('%H')
    timestamp = int(X.t.timestamp())
    filepath = f"{outputpath}{date}/{hour}/"
    filename = f"{filepath}{timestamp}.jpg"
    SaveImage(X.image, filepath, filename)

    train_images_query = """INSERT INTO train_images
    (image_id,event_id,filename,dateTime,type)
    VALUES (%s,%s,%s,%s,%s);
    """
    train_images_data = [image_id,event_id,filename,int(X.timestamp),state.value]
    database.ExecuteQuery(train_images_query, train_images_data)

class Logger:

    def __init__(self, ARGS):

        self.ARGS = ARGS
        self.classify_history_deque = deque(maxlen=ARGS.len_classify_history_deque)
        self.classify_history_sum = 0
        self.state = LoggerState.train_event_off
        self.next_valid_event_id = ARGS.latest_event_id + 1
        self.next_valid_image_id = ARGS.latest_image_id + 1
        self.frame_count = 0
        self.frame_threshold = ARGS.frame_threshold_train_event_off
        self.event_id = -1

    def G(self, is_train_p):

        '''
            This is the activation function for a LoggerState transitions.
            Input: X.is_train_p: value between 0.0-1.0 - from the main camera script.
            Output: Destination LoggerState
        '''
        if len(self.classify_history_deque) > 0:
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

        if self.state != dest_state:
            # reset frame_count and frame_threshold for all transitions
            self.frame_count = 0
            if dest_state == LoggerState.train_event_on:
                self.frame_threshold = self.ARGS.frame_threshold_train_event_on
            elif dest_state == LoggerState.train_event_off:
                self.frame_threshold = self.ARGS.frame_threshold_train_event_ff
            else:
                self.frame_threshold = self.ARGS.frame_threshold_train_event_stationary

        # reset event_id when event completes
        if self.state == LoggerState.train_event_on and dest_state != LoggerState.train_event_on:
            self.event_id = -1
        elif self.state == LoggerState.stationary and dest_state == LoggerState.train_event_off:
            self.event_id = -1

        self.state = dest_state

    def ShouldSave(self):

        if self.frame_count % self.frame_threshold == 0:
            return True

    def Input(self, X):

        '''
            This is the main logger input function for a camera frame.
            Input: X - from the main camera script.
                    Dictionary: {image: PIL Image,
                                 is_train_p: [0.0-1.0],
                                 timestamp: UNIX timestamp}
            Output: None.
        '''
        self.frame_count += 1
        dest_state = self.G(X.is_train_p)
        self.ChangeState(dest_state)

        if self.ShouldSaveFrame():
            # Make sure event_id is valid for train_event_on & stationary events
            if self.event_id == -1 and self.state != LoggerState.train_event_off:
                self.event_id = self.next_valid_event_id
                self.next_valid_event_id += 1

            SaveFrame(X, self.state, self.event_id, self.next_valid_image_id, self.ARGS.outputpath)
            self.next_valid_image_id += 1



