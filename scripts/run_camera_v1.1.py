import argparse
import configparser
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
import database_config
import mysql.connector
from mysql.connector import errorcode
import purple_air_sql as pa
import met_sql as met

import time
from threading import Thread
from concurrent.futures import Future

from os import makedirs

import math
import heapq
from scipy.spatial import distance as dist

import copy
import sys

# for fps calculations
start_t = time.time()
frame_times = []
last_time = time.time()

DATA_ARR = []
LABELS = []
COLLECT_FREQUENCY = 10

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

def gstreamer_pipeline(
	capture_width=300,
	capture_height=300,
	display_width=300,
	display_height=300,
	framerate=21,
	flip_method=0,
	):
	return (
		"nvarguscamerasrc ! "
		"video/x-raw(memory:NVMM), "
		"width=(int)%d, height=(int)%d, "
		"format=(string)NV12, framerate=(fraction)%d/1 ! "
		"nvvidconv flip-method=%d ! "
		"video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
		"videoconvert ! "
		"video/x-raw, format=(string)BGR ! appsink"
		% (
			capture_width,
			capture_height,
			framerate,
			flip_method,
			display_width,
			display_height,
		)
	)

# for debuggin
def display_image(IMAGE, BOX, LABEL, SCORE, FPS, TRACKING):
	if TRACKING:
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), (0,0,255), 5)
	else:
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), (255,0,0), 5)
	(startX, startY, endX, endY) = BOX
	y = startY - 40 if startY - 40 > 40 else startY + 40
	text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
	font = cv2.FONT_HERSHEY_SIMPLEX
	cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)
	pa_data = pa.get_latest_data()
	cv2.putText(IMAGE, 'pm2.5=' + str(pa_data['pm2.5']), (20,20), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	met_data = met.get_latest_data()
	cv2.putText(IMAGE, 'windGust=' + str(met_data['windGust']) + 'mph', (20,40), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.putText(IMAGE, 'wgDir=' + str(met_data['windGustDir'] if met_data['windGustDir'] else 'null'), (20,60), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)

# for debugging
def get_fps() -> float: # returns (fps,start_t)
	global frame_times
	global start_t
	end_t = time.time()
	time_taken = end_t - start_t
	frame_times.append(time_taken)
	frame_times = frame_times[-20:]
	fps = 20 / sum(frame_times)
	start_t = time.time()
	return fps

def debug(DETECT, BOX, FPS, IMAGE, TIMESTAMP, TRACKING):
	# coords = dict(zip(['startX', 'startY', 'endX', 'endY'], BOX))
	# dataline = str(TIMESTAMP) + ', ' + LABELS[DETECT.label_id] + ', conf = ' + str(DETECT.score) + ', coords = ' + str(coords) + '\n'
	# print(dataline)
	BOX = list(BOX)
	BOX = [int(_) for _ in BOX]
	display_image(IMAGE, BOX, LABELS[DETECT.label_id], DETECT.score, FPS, TRACKING)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		return

def debug_mul(MOVING_DETECTS, STAT_DETECTS, IMAGE, FPS):
	# print('called debug_mul')
	def put_lines(IMAGE, BOX, LABEL, SCORE, BOX_COLOR_BGR):
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), BOX_COLOR_BGR, 5)
		(startX, startY, endX, endY) = BOX
		y = startY - 40 if startY - 40 > 40 else startY + 40
		text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)
	for i,box in enumerate(MOVING_DETECTS.bounding_boxes):
		put_lines(IMAGE, box.flatten().astype('int'), 'train', MOVING_DETECTS.scores[i], (0,0,255)) # moving box is red color
	for i,box in enumerate(STAT_DETECTS.bounding_boxes):
		put_lines(IMAGE, box.flatten().astype('int'), 'train', STAT_DETECTS.scores[i], (255,0,0))
		#put_lines(IMAGE, d.bounding_box.flatten().astype('int'), 'train', d.score, (255,0,0)) # stat box is bllue color
		# cv2.circle(IMAGE, (int(st[0]),int(st[1])), radius=10, color=(0, 0, 255), thickness=-1)
	cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# font = cv2.FONT_HERSHEY_SIMPLEX
	# pa_data = pa.get_latest_data()
	# cv2.putText(IMAGE, 'pm2.5=' + str(pa_data['pm2.5']), (20,20), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# met_data = met.get_latest_data()
	# cv2.putText(IMAGE, 'windGust=' + str(met_data['windGust']) + 'mph', (20,40), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# cv2.putText(IMAGE, 'wgDir=' + str(met_data['windGustDir'] if met_data['windGustDir'] else 'null'), (20,60), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)

@threaded
def run_insert_query(query, data):
	CNX = database_config.connection()
	try:
		cursor = CNX.cursor()
		cursor.execute(query, data)
	except mysql.connector.Error as err:
		print(err)
		return -1
	CNX.commit()
	#event_id = dict(zip(cursor.column_names, cursor.fetchone()))[id]
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

	def __init__(self, collect_rate_moving=0.1, collect_rate_stat=0.001, empty_frames_limit=50, max_stat_entries=2000, moving_trains_conf=0.7):
		self.empty_frames_limit = empty_frames_limit
		self.moving_trains_conf = moving_trains_conf
		self.max_stat_entries = max_stat_entries
		self.collect_rate_moving = collect_rate_moving
		self.collect_rate_stat = collect_rate_stat

	def log(self, image, moving_trains, stationary_trains, timestamp = datetime.now().timestamp()):
		if moving_trains.len() + stationary_trains.len() > 0:
			entry = LogEntry(timestamp, image, moving_trains, stationary_trains)
			self.entries.append(entry)
		# print(sys._getframe().f_lineno)
		if self.train_event_on:
			# check if we hit max empty frames
			if moving_trains.len() == 0:
				self.frames += 1
			else:
				self.frames = 0
			if self.frames >= self.empty_frames_limit:
				print('-----------------------------train event off-----------------------------')

				self.frames = 0
				self.count_from_first_moving = 0
				self.train_event_on = False
				# log entries and previous entries now
				self.save_train_event(self.entries, self.collect_rate_moving)
				self.entries = []
				self.save_train_event(self.previous_entries, self.collect_rate_stat)
				self.previous_entries = []
		elif moving_trains.len() + stationary_trains.len() > 0:
			if moving_trains.len() > 0:
				# switch to train_event_on
				self.frames = 0
				self.train_event_on = True
				print('train event on')
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
				# print(sys._getframe().f_lineno)
				self.frames += 1
				self.count_from_first_moving += 1 if self.count_from_first_moving == 0 else 0

	@threaded
	def save_train_event(self, entries, collect_rate):
		# first downsize entries
		print('---------')
		print(entries[0].timestamp)
		print(entries[-1].timestamp)
		start_timestamp = int(math.floor(entries[0].timestamp))
		end_timestamp = int(math.ceil(entries[-1].timestamp))
		print('saving train event - 1111')
		print('len entries = ' + str(len(entries)))
		# print('collect_rate = ' + str(collect_rate))
		# print('len(entries)*collect_rate=' + str(int(collect_rate*len(entries))))
		indices = np.random.randint(len(entries), size=max(int(collect_rate*len(entries)),1))
		print(indices)
		entries = [entry for i,entry in enumerate(entries) if i in indices]
		if len(entries) > 0:
			# print('len entries > 0')
			# save moving trains
			#first setup event start and end timestamps
			start_timestamp = int(math.floor(entries[0].timestamp))
			end_timestamp = int(math.ceil(entries[-1].timestamp))
			# now create a moving train event record in database
			query = """INSERT INTO train_events
				(start,end)
				VALUES (%s,%s);
			"""
			event_id = run_insert_query(query, [start_timestamp,end_timestamp]).result()
			# now insert images into database ans save them on disk
			print('returned event_id = ' + str(event_id))
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
		image_id = run_insert_query(query, [filename, event_id]).result()
		# now insert into train_detects, moving trains and stationary trains
		DATA = []
		for i in range(entry.moving_trains.len()):
			values = [event_id, 1, image_id, 'train', entry.moving_trains.scores[i]]
			values.extend(entry.moving_trains.bounding_boxes[i].flatten().astype("int").tolist())
			DATA.append(values)
			print(values)
		for i in range(entry.stationary_trains.len()):
			values = [event_id, 2, image_id, 'train', entry.stationary_trains.scores[i]]
			values.extend(entry.stationary_trains.bounding_boxes[i].flatten().astype("int").tolist())
			DATA.append(values)
			print(values)
		query = """INSERT INTO train_detects
				(event_id, type, image_id, label, score, x0, y0, x1, y1)
				VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
		"""
		CNX = database_config.connection()
		try:
			cursor = CNX.cursor()
			cursor.executemany(query, DATA)
		except mysql.connector.Error as err:
			print(err)
			return
		CNX.commit()
	@threaded
	def save_image(self, IMAGE, FILENAME, FILEPATH):
		print('saving image')
		output_path = "/home/coal/Desktop/output/"
		try:
			makedirs(output_path + FILEPATH)
		except FileExistsError:
			_=1
		if not cv2.imwrite(output_path+FILENAME, IMAGE):
			print('----error saving image----')



def match_min_dist(row_vector, col_vector, dist_limit):
	# row_vector and col_vector are numpy arrays of points.
	# dist.cdist calculates euclidean distance between each
	# pair of points in row and col and returns a m*n matirx.
	# m = len(row_vector), n = len(col_vector)
	D = dist.cdist(row_vector, col_vector)
	# amin(D, axis=1) returns a column vector with minimum values of each row
	mins = np.amin(D, axis=1)
	# we want the indices of the columns in which the row-minimums occur
	cols = [np.where(D[i] == mins[i])[0][0] for i in range(mins.shape[0])]
	# create a list of nested tuples 
	min_heap = [(mins[row], (row,col)) for row,col in enumerate(cols)] # creating list of nested tuple - (min_value, (row,col))
	# sort the tuples using a minheap, sorting by distance ascending
	heapq.heapify(min_heap)
	# keep track of matched pairs because we want them to be unique! (unique row,unique col)
	used_cols = set()
	used_rows = []
	while len(min_heap) > 0:
		(min_value,(row,col)) = heapq.heappop(min_heap)
		if min_value < dist_limit:
			# we only check for col in used_cols because rows are already unique, we made a column vector for min cols in each row.
			if col not in used_cols:
				used_cols.add(col)
				used_rows.append(row)
			else:
				continue
	return (used_rows, used_cols)

class trains: # object to hold info about detected trains
	bounding_boxes = []
	centroids = []
	empty_frames = []
	scores = []

	def __init__(self, l_bounding_box = [], l_centroid = [], l_scores = [], l_empty_frames = []):
		self.bounding_boxes = l_bounding_box
		self.centroids = l_centroid
		self.empty_frames = l_empty_frames
		# print("len centroids = " + str(len(self.centroids)))
		# print("len empty_frames = " + str(len(self.empty_frames)))
		self.scores = l_scores
		# print('l_bounding_box = ' + str(len(l_bounding_box)))
		#self.print_lens()

	def add(self, bounding_box, centroid, score, frames = 0):
		self.bounding_boxes.append(bounding_box)
		self.centroids.append(centroid)
		self.empty_frames.append(frames)
		self.scores.append(score)

	def remove_at(self, index):
		if index < len(self.centroids):
			del self.bounding_boxes[index]
			del self.centroids[index]
			del self.empty_frames[index]
			del self.scores[index]

	def len(self):
		return len(self.centroids)

	def copy(self, target):
		self.bounding_boxes = copy.deepcopy(target.bounding_boxes)
		self.centroids = copy.deepcopy(target.centroids)
		self.empty_frames = copy.deepcopy(target.empty_frames)
		self.scores = copy.deepcopy(target.scores)

	def extend(self, target, refresh = False):
		if refresh:
			self.bounding_boxes = []
			self.centroids = []
			self.empty_frames = []
			self.scores = []
		self.bounding_boxes.extend(target.bounding_boxes)
		self.centroids.extend(target.centroids)
		self.empty_frames.extend(target.empty_frames)
		self.scores.extend(target.scores)

	def filter_out(self, indices):
		self.bounding_boxes = [b for i,b in enumerate(self.bounding_boxes) if i not in indices]
		self.centroids = [c for i,c in enumerate(self.centroids) if i not in indices]
		self.empty_frames = [f for i,f in enumerate(self.empty_frames) if i not in indices]
		self.scores = [s for i,s in enumerate(self.scores) if i not in indices]

	def filter_stationary(self, used_indices, EFD): # returns new object with filtered data
		# used rows/indices = stationary centroids that were matched with train detects in current frames.
		# We need to retain those.
		# Also retain centroids that have not been detected for up
		# to EFD frames (Empty Frames for Detection).
		temp = trains(l_bounding_box = [], l_centroid = [], l_scores = [], l_empty_frames = [])
		for i in range(self.len()):
			if i in used_indices:
				temp.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], 0)
			elif self.empty_frames[i] < EFD:
				temp.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], self.empty_frames[i]+1)
		self.copy(temp)

	def filter_previous(self, used_indices, EFT, stat_trains):
		# used indecices = previous centroids that are matched with current detects.
		# these previous centroids need to be marked as stationary trains.
		# previous centroids not matched with a train detect for more \
		# than EFT (Empty Frames for Tracking) consecutive frames will be discarded.
		temp_previous = trains(l_bounding_box = [], l_centroid = [], l_scores = [], l_empty_frames = [])
		for i in range(self.len()):
			if i in used_indices:
				stat_trains.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], 0)
			elif self.empty_frames[i] < EFT:
				temp_previous.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], self.empty_frames[i]+1)
		self.extend(temp_previous, refresh = True)
		# self.copy(temp_previous)

	def print_lens(self):
		print('-----lenghts------')
		print('bounding_boxes = ' + str(len(self.bounding_boxes)))
		print('centroids = ' + str(len(self.centroids)))
		print('empty_frames = ' + str(len(self.empty_frames)))
		print('scores = ' + str(len(self.scores)))


def loop(STREAM, ENGINE, DEBUG, CONF, DTS, DDS, EFT, EFD, DFPS):
	CONF = CONF/100
	stationary_centroids = [[],[]] # [centroid][consecutive empty frames]
	previous_centroids = [[],[]]

	stationary_trains = trains()
	previous_trains = trains()
	logger = Logger()

	total_moving_detects = 0
	while STREAM.isOpened():
		fps = get_fps()
		if DFPS and not DEBUG:
			print('fps = ' + str(fps))
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		_, image = STREAM.read()
		detections = ENGINE.detect_with_image(Image.fromarray(image), threshold=CONF, top_k=10, keep_aspect_ratio=True, relative_coord=False)
		train_detects = [d for d in detections if d.label_id == 6]
		# if len(train_detects) == 0:
		# 	print('no detects')
		# 	continue
		train_centroids = []
		current_trains = trains()
		if len(train_detects) > 0:
			train_centroids = (np.array([d.bounding_box for d in train_detects])).sum(axis=1) / 2

		current_trains = trains([d.bounding_box for d in train_detects], train_centroids, [int(d.score*100) for d in train_detects], [0 for _ in train_detects])

		# Step 1 - Discounting previously recognized stationary trains from the current train detects .
		if stationary_trains.len() > 0:
			# Calculate distances between each pair of train detect centroids and stationary centroids.
			# Sort pairs by minimum distance and match unique paris with distances less
			# than DDS (Detect to Stationary Distance).
			used_rows, used_cols = [],[]
			if current_trains.len() > 0:
				(used_rows, used_cols) = match_min_dist(row_vector=np.array(stationary_trains.centroids),
														col_vector=current_trains.centroids, dist_limit=DDS)
			current_trains.filter_out(used_cols)
			stationary_trains.filter_stationary(used_rows, EFD)
		# Step 2 - Recognizing new stationary trains by comparing centroids from previous frames
		if previous_trains.len() > 0:
			# Calculate distances between each pair of (filtered) train detect centroids and stationary centroids.
			# Sort pairs by minimum distance and match unique paris with distances less
			# than DTS (Tracking to Stationary Distance).
			used_rows, used_cols = [],[]
			if current_trains.len() > 0:
				(used_rows, used_cols) = match_min_dist(row_vector=np.array(previous_trains.centroids),
													col_vector=np.array(current_trains.centroids), dist_limit=DTS)
			current_trains.filter_out(used_cols)
			previous_trains.filter_previous(used_rows, EFT, stationary_trains)
		previous_trains.extend(current_trains)
		# if current_trains.len() + stationary_trains.len() > 0:
			# print('logging')
			# print('fps = ' + str(fps))
		logger.log(image = image, moving_trains = current_trains, stationary_trains = stationary_trains, timestamp=datetime.now().timestamp())
		if DEBUG and not DFPS:
			# print(".........")
			# print(str(current_trains.len()) + ',  ' + str(previous_trains.len()) + ',  ' + str(stationary_trains.len()))
			debug_mul(current_trains, stationary_trains, image, fps)
			keyCode = cv2.waitKey(1) & 0xFF
			# Stop the program on the 'q' key
			if keyCode == ord("q"):
				break
		# print("....!....")
		if DEBUG and DFPS:
			print('total_moving_detects = ' + str(total_moving_detects))



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
	PARSER.add_argument('-o', '--output_path', action='store', default='/home/coal/Desktop/output/', help="Path to output directory.")
	PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
	PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
	PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")
	PARSER.add_argument('-conf', '--confidence', action='store', type=int, default=20, help="Detection confidence level out of 100.")
	PARSER.add_argument('-dts', '--dts', action='store', type=float, default=1, help="distance tracking to stationary.")
	PARSER.add_argument('-dds', '--dds', action='store', type=int, default=1, help="distance detect to stationary.")
	PARSER.add_argument('-eft', '--eft', action='store', type=int, default=20, help="empty frames allowed for tracking.")
	PARSER.add_argument('-efd', '--efd', action='store', type=int, default=40, help="empty frames allowed for detection.")
	
	PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")
	PARSER.add_argument('-dfps', '--debugonlyfps', action='store_true', default=False, help="Debug Mode - Only FPS")

	ARGS = PARSER.parse_args()
	# Load the DetectionEngine
	ENGINE = DetectionEngine(ARGS.model)
	if not ENGINE:
		print("Failed to load detection engine.")
		exit()
	# Read labels file
	LABELS = dataset_utils.read_label_file(ARGS.label)
	if not LABELS:
		print("Failed to load labels file")
		exit()
	# Setup image capture stream
	STREAM = cv2.VideoCapture(gstreamer_pipeline(capture_width = ARGS.width, capture_height = ARGS.height, display_width = ARGS.width, display_height = ARGS.height, framerate=ARGS.fps), cv2.CAP_GSTREAMER)

	try:
		if not STREAM.isOpened():
			STREAM.open()
		loop(STREAM, ENGINE, ARGS.debug, ARGS.confidence, ARGS.dts,
			 ARGS.dds, ARGS.eft, ARGS.efd, ARGS.debugonlyfps)
		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()








