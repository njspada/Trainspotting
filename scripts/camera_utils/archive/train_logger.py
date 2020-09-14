from threading import Thread
from concurrent.futures import Future
import cv2
import numpy as np
from datetime import datetime
import mysql.connector
from mysql.connector import errorcode
from os import makedirs
import math

# threading related source from - 
# https://stackoverflow.com/questions/19846332/python-threading-inside-a-class
def call_with_future(fn, future, args, kwargs):
    try:
        result = fn(*args, **kwargs)
        future.set_result(result)
    except Exception as exc:
        future.set_exception(exc)

def threaded(fn):
    def wrapper(*args, **kwargs):
        future = Future()
        Thread(target=call_with_future, args=(fn, future, args, kwargs)).start()
        return future
    return wrapper

@threaded
def run_insert_query(query, data, database_config):
    CNX = database_config.connection()
    try:
        cursor = CNX.cursor()
        cursor.execute(query, data)
    except mysql.connector.Error as err:
        print(err)
        return -1
    CNX.commit()
    return cursor.lastrowid

class LogEntry:
    image = None
    timestamp = ""
    db_id = ""
    moving_trains = None
    stationary_trains = None

    def __init__(self,t,i,mt,st):
        self.image = i
        self.timestamp = t
        self.moving_trains = mt
        self.stationary_trains = st

class Logger:
    train_event_on = False
    frames = 0 # when train_event_on: count consecutive empty frames, else count moving frames
    entries = [] # [train_image]
    previous_entries = []
    empty_frames_limit = 20 # used to switch from moving event to empty/stationary event
    moving_trains_conf = 0.7 # used to switch from empty/stationary event to moving event
    count_from_first_moving = 0 # number of frames 
    max_stat_entries = 200
    collect_rate_moving = 0.1
    collect_rate_stat = 0.001
    database_config = []
    debug = False

    def __init__(self, ARGS, database_config):
        self.empty_frames_limit  = ARGS.empty_frames_limit
        self.moving_trains_conf  = ARGS.moving_trains_conf
        self.max_stat_entries    = ARGS.max_stat_entries
        self.collect_rate_moving = ARGS.collect_rate_moving
        self.collect_rate_stat   = ARGS.collect_rate_stat
        self.database_config     = database_config
        # self.debug               = ARGS.debug
        self.debug = True
        self.output_path         = ARGS.output_path

    # prints only when debugging
    def print(self, to_print,force=False):
        if self.debug or forece:
            print(to_print)

    def log(self, image, moving_trains, stationary_trains, timestamp = datetime.now().timestamp()):
        if moving_trains.len() + stationary_trains.len() > 0:
            entry = LogEntry(timestamp, image, moving_trains, stationary_trains)
            self.entries.append(entry)
        if self.train_event_on:
            # check if we hit max empty frames
            if moving_trains.len() == 0:
                self.frames += 1
            else:
                self.frames = 0
            if self.frames >= self.empty_frames_limit:
                self.print('-----------------------------train event off-----------------------------')
                self.frames = 0
                self.count_from_first_moving = 0
                self.train_event_on = False
                # log entries and previous entries now
                # don't save stationary trains for moving event
                # self.entries.stationary_trains = []
                # make sure entries have at least one moving train
                self.entries = [LogEntry(e.timestamp,e.image,e.moving_trains,[]) for e in self.entries if e.moving_trains.len() > 0]
                self.save_train_event(self.entries, self.collect_rate_moving)
                self.entries = []
                self.save_train_event(self.previous_entries, self.collect_rate_stat)
                self.previous_entries = []
        elif moving_trains.len() + stationary_trains.len() > 0:
            if moving_trains.len() > 0:
                # switch to train_event_on
                self.frames = 0
                self.train_event_on = True
                self.print('train event on')
                self.count_from_first_moving = 1
                # store non train event frames in buffer, write back after train event 
                self.previous_entries = self.entries[:-self.count_from_first_moving]
                self.entries = self.entries[-self.count_from_first_moving:]
            elif len(self.entries) > self.max_stat_entries:
                # get rid of older entries that are not part of potential moving event
                self.save_train_event(self.entries, self.collect_rate_stat)
                self.entries = []
                self.frames = 0
                self.count_from_first_moving = 0
            elif moving_trains.len() > 0:
                self.frames += 1
                self.count_from_first_moving += 1 if self.count_from_first_moving == 0 else 0

    @threaded
    def save_train_event(self, entries, collect_rate):
        # first downsize entries
        if len(entries) == 0:
            return
        self.print('-----0----')
        self.print('len entries = ' + str(len(entries)))
        self.print(str(entries[0].timestamp))
        self.print('-----1----')
        self.print(str(entries[-1].timestamp))
        self.print('----2-----')
        start_timestamp = int(math.floor(entries[0].timestamp))
        self.print('----3-----')
        end_timestamp = int(math.ceil(entries[-1].timestamp))
        self.print('----4-----')
        self.print('saving train event - 1111')
        indices = np.random.randint(len(entries), size=max(int(collect_rate*len(entries)),1))
        self.print(indices)
        entries = [entry for i,entry in enumerate(entries) if i in indices]
        if len(entries) > 0:
            # save moving trains
            #first setup event start and end timestamps
            start_timestamp = int(math.floor(entries[0].timestamp))
            end_timestamp = int(math.ceil(entries[-1].timestamp))
            # now create a moving train event record in database
            query = """INSERT INTO train_events
                (start,end)
                VALUES (%s,%s);
            """
            event_id = run_insert_query(query, [start_timestamp,end_timestamp], self.database_config).result()
            # now insert images into database ans save them on disk
            self.print('returned event_id = ' + str(event_id))
            for entry in entries:
                self.insert_entry(entry, event_id)
    @threaded
    def insert_entry(self, entry, event_id):
        t = datetime.fromtimestamp(entry.timestamp)
        date = t.strftime('%Y-%m-%d')
        hour = t.strftime('%H')
        filepath = date + '/' + hour + '/' + str(event_id) + '/'
        filename = filepath + str(entry.timestamp) + '.jpg'
        self.save_image(entry.image, filename, filepath)
        query = """INSERT INTO train_images
                (filename, event_id)
                VALUES (%s,%s);
        """             
        image_id = run_insert_query(query, [filename, event_id], self.database_config).result()
        # now insert into train_detects, moving trains and stationary trains
        DATA = []
        for i in range(entry.moving_trains.len()):
            values = [event_id, 1, image_id, 'train', entry.moving_trains.scores[i]]
            values.extend(entry.moving_trains.bounding_boxes[i].flatten().astype("int").tolist())
            DATA.append(values)
            self.print(values)
        for i in range(entry.stationary_trains.len()):
            values = [event_id, 2, image_id, 'train', entry.stationary_trains.scores[i]]
            values.extend(entry.stationary_trains.bounding_boxes[i].flatten().astype("int").tolist())
            DATA.append(values)
            self.print(values)
        query = """INSERT INTO train_detects
                (event_id, type, image_id, label, score, x0, y0, x1, y1)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """
        CNX = self.database_config.connection()
        try:
            cursor = CNX.cursor()
            cursor.executemany(query, DATA)
        except mysql.connector.Error as err:
            self.print(err,force=True)
            return
        CNX.commit()

    @threaded
    def save_image(self, IMAGE, FILENAME, FILEPATH):
        self.print('saving image')
        try:
            makedirs(self.output_path + FILEPATH)
        except FileExistsError:
            _=1
        if not cv2.imwrite(self.output_path+FILENAME, IMAGE):
            print('----error saving image----')