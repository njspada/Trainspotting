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
import threading

from os import mkdir

import math
import heapq
from scipy.spatial import distance as dist

# for fps calculations
start_t = time.time()
frame_times = []
last_time = time.time()

DATA_ARR = []
LABELS = []
COLLECT_FREQUENCY = 10

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
	def put_lines(IMAGE, BOX, LABEL, SCORE, BOX_COLOR_BGR):
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), BOX_COLOR_BGR, 5)
		(startX, startY, endX, endY) = BOX
		y = startY - 40 if startY - 40 > 40 else startY + 40
		text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)
	for d in MOVING_DETECTS:
		put_lines(IMAGE, d.bounding_box.flatten().astype('int'), 'train', d.score, (0,0,255)) # moving box is red color
	for st in STAT_DETECTS:
		#put_lines(IMAGE, d.bounding_box.flatten().astype('int'), 'train', d.score, (255,0,0)) # stat box is bllue color
		cv2.circle(IMAGE, (int(st[0]),int(st[1])), radius=10, color=(0, 0, 255), thickness=-1)
	cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# font = cv2.FONT_HERSHEY_SIMPLEX
	# pa_data = pa.get_latest_data()
	# cv2.putText(IMAGE, 'pm2.5=' + str(pa_data['pm2.5']), (20,20), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# met_data = met.get_latest_data()
	# cv2.putText(IMAGE, 'windGust=' + str(met_data['windGust']) + 'mph', (20,40), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# cv2.putText(IMAGE, 'wgDir=' + str(met_data['windGustDir'] if met_data['windGustDir'] else 'null'), (20,60), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)

def save_image(IMAGE, FILENAME):
	print('saving image')
	output_path = "/home/coal/Desktop/output/"
	cv2.imwrite(output_path+FILENAME, IMAGE)
	
def store_a_train_detect(DETECTS, FILENAME, EVENT_ID):
	global LABELS
	print(DETECTS[0].bounding_box.flatten().astype("int"))
	DATA = [[EVENT_ID, FILENAME, LABELS[d.label_id], float(d.score)]
			.extend(DETECTS[0].bounding_box.flatten().astype("int"))
			 for d in DETECTS]
	CNX = database_config.connection()
	if not CNX:
		print('Failed to connect to MySQL database!')
		exit()
	query = """INSERT INTO images  
				(event_id, filename, label, conf, `x0`, `y0`, `x1`, `y1`) 
				VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""";
	try:
		cursor = CNX.cursor()
		cursor.executemany(query, DATA)
	except mysql.connector.Error as err:
		print(err)
	else:
		CNX.commit()

def store_train_event(DETECT_LIST):# [[image, [train_detects], timestamp]]
	print('storing train event')
	start = DETECT_LIST[0][2]
	end = DETECT_LIST[-1][2]
	query = """INSERT INTO train_events
				(start,end)
				VALUES (%s,%s);
			"""
	CNX = database_config.connection()
	try:
		cursor = CNX.cursor()
		cursor.execute(query, [start,end])
	except mysql.connector.Error as err:
		print(err)
	else:
		CNX.commit()
		#event_id = dict(zip(cursor.column_names, cursor.fetchone()))[id]
		event_id = cursor.lastrowid
		mkdir('/home/coal/Desktop/output/' + str(event_id))
		global COLLECT_FREQUENCY
		l = int(len(DETECT_LIST)/COLLECT_FREQUENCY)
		for i in range(0,l):
			filename = str(event_id) + '/' + str(DETECT_LIST[i*COLLECT_FREQUENCY][2]) + '.jpg'
			t0 = threading.Thread(target=store_a_train_detect, args=(DETECT_LIST[i*COLLECT_FREQUENCY][1], filename, event_id,))
			t1 = threading.Thread(target=save_image, args=(DETECT_LIST[i*COLLECT_FREQUENCY][0],filename,))
			t0.start()
			t1.start()

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

def loop(STREAM, ENGINE, DEBUG, CONF, DTS, DDS, EFT, EFD, DFPS):
	CONF = CONF/100
	stationary_centroids = [[],[]] # [centroid][consecutive empty frames]
	previous_centroids = [[],[]]
	while STREAM.isOpened():
		fps = get_fps()
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		_, image = STREAM.read()
		detections = ENGINE.detect_with_image(Image.fromarray(image), threshold=CONF, top_k=10, keep_aspect_ratio=True, relative_coord=False)
		train_detects = [d for d in detections if d.label_id == 6]
		if len(train_detects) == 0:
				continue
		train_centroids = (np.array([d.bounding_box for d in train_detects])).sum(axis=1) / 2
		# Step 1 - Discounting previously recognized stationary trains from the current train detects .
		if len(stationary_centroids[0]) > 0:
			# Calculate distances between each pair of train detect centroids and stationary centroids.
			# Sort pairs by minimum distance and match unique paris with distances less
			# than DDS (Detect to Stationary Distance).
			(used_rows, used_cols) = match_min_dist(row_vector=np.array(stationary_centroids[0]),
													col_vector=train_centroids, dist_limit=DDS)
			train_detects = [d for col,d in enumerate(train_detects) if col not in used_cols]
			train_centroids = [c for col,c in enumerate(train_centroids) if col not in used_cols]
			temp_st = [[],[]]
			def filter_st(row):
				# used rows = stationary centroids that were matched with train detects in current frames.
				# We need to retain those.
				# Also retain centroids that have not been detected for up
				# to EFD frames (Empty Frames for Detection).
				if row in used_rows or stationary_centroids[1][row] < EFD:
					temp_st[0].append(stationary_centroids[0][row])
					temp_st[1].append(0 if row in used_rows else stationary_centroids[1][row]+1)
			_ = [filter_st(row) for row in range(len(stationary_centroids[0]))]
			stationary_centroids = temp_st
		# Step 2 - Recognizing new stationary trains by comparing centroids from previous frames
		if len(previous_centroids[0]) > 0 and len(train_centroids) > 0:
			# Calculate distances between each pair of (filtered) train detect centroids and stationary centroids.
			# Sort pairs by minimum distance and match unique paris with distances less
			# than DTS (Tracking to Stationary Distance).
			(used_rows, used_cols) = match_min_dist(row_vector=np.array(previous_centroids[0]),
													col_vector=np.array(train_centroids), dist_limit=DTS)
			train_detects = [d for col,d in enumerate(train_detects) if col not in used_cols]
			train_centroids = [c for col,c in enumerate(train_centroids) if col not in used_cols]
			temp_previous = [[],[]]
			def filter_previous_update_stationary(row):
				# used rows = previous centroids that are matched with current detects.
				# these previous centroids need to be marked as stationary trains.
				# previous centroids not matched with a train detect for more \
				# than EFT (Empty Frames for Tracking) consecutive frames will be discarded.
				if row in used_rows:
					stationary_centroids[0].append(previous_centroids[0][row])
					stationary_centroids[1].append(0)
				elif previous_centroids[1][row] < EFT:
					temp_previous[0].append(previous_centroids[0][row])
					temp_previous[1].append(previous_centroids[1][row]+1)
			_ = [filter_previous_update_stationary(row) for row in range(len(previous_centroids[0]))]
			previous_centroids = temp_previous
		previous_centroids[0].extend(train_centroids)
		previous_centroids[1].extend([0 for _ in range(len(train_centroids))])
		if DEBUG and not DFPS:
			debug_mul(train_detects, stationary_centroids[0], image, fps)
			keyCode = cv2.waitKey(1) & 0xFF
			# Stop the program on the 'q' key
			if keyCode == ord("q"):
				break
		if DFPS:
			print('fps = ' + str(fps))



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
	PARSER.add_argument('-o', '--output_path', action='store', default='/home/coal/Desktop/output/', help="Path to output directory.")
	PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
	PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
	PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")
	PARSER.add_argument('-conf', '--confidence', action='store', type=int, default=20, help="Detection confidence level out of 100.")
	PARSER.add_argument('-dts', '--dts', action='store', type=int, default=1, help="distance tracking to stationary.")
	PARSER.add_argument('-dds', '--dds', action='store', type=int, default=5, help="distance detect to stationary.")
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








