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
from scipy.spatial import distance as dist

import heapq

start_t = time.time()
frame_times = []

last_time = time.time()

DATA_ARR = []
LABELS = []
COLLECT_FREQUENCY = 10

OPENCV_OBJECT_TRACKERS = {}

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
def display_image(IMAGE, BOX, LABEL, SCORE, FPS, COLOR_BGR):
	# if TRACKING:
	# 	cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), (0,0,255), 5)
	# else:
	# 	cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), (255,0,0), 5)
	cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), COLOR_BGR, 5)
	(startX, startY, endX, endY) = BOX
	y = startY - 40 if startY - 40 > 40 else startY + 40
	text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
	font = cv2.FONT_HERSHEY_SIMPLEX
	cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)
	# pa_data = pa.get_latest_data()
	# cv2.putText(IMAGE, 'pm2.5=' + str(pa_data['pm2.5']), (20,20), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# met_data = met.get_latest_data()
	# cv2.putText(IMAGE, 'windGust=' + str(met_data['windGust']) + 'mph', (20,40), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# cv2.putText(IMAGE, 'wgDir=' + str(met_data['windGustDir'] if met_data['windGustDir'] else 'null'), (20,60), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)

def add_to_image(IMAGE, BOX, LABEL, SCORE, COLOR_BGR):
	cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), COLOR_BGR, 5)
	(startX, startY, endX, endY) = BOX
	y = startY - 40 if startY - 40 > 40 else startY + 40
	text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
	font = cv2.FONT_HERSHEY_SIMPLEX
	cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)

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

def debug_multi(DETECTS, TRAIN_DETECT, STATIONARY, FPS, IMAGE):
	if TRAIN_DETECT:
		add_to_image(IMAGE, TRAIN_DETECT.bounding_box, 'train', TRAIN_DETECT.score, (0,255,0))
	for d in DETECTS:
		add_to_image(IMAGE, d.bounding_box, 'detect', d.score, (255,0,0))
	for st in STATIONARY:
		# add_to_image(IMAGE, st, 'stat', 0, (0,0,255))
		cv2.circle(IMAGE, st, radius=0, color=(0, 0, 255), thickness=-1)
	cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		return

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

def box2centroid(box):
	(startX,startY,endX,endY) = box
	cX = int((startX + endX) / 2.0)
	cY = int((startY + endY) / 2.0)
	return [cX,cY]

def ydist(oldBox,newBox):
	oldP = box2centroid(oldBox)
	newP = box2centroid(newBox)
	return math.hypot(oldP[0]-newP[0],oldP[1]-newP[1])


# stationary_trains - list of train objects that are identified as stationary
# 1. When we are not tracking any trains, use detection engine to detect all train objects in the current frame
#    Then discount all the newly detected trains that can be matched with stationary trains.
#    Discount any unmatched stationary_trains
#    Ideally there should be only one remaining train detect that is not stationary, attach tracker to this train
# 2. When tracking a train, there two cases - 
#    a. The tracker lost the object. Make use of empty frame buffer here. 
#           If tracker returns failure for more than EMPTY_FRAMES limit, then the train is no longer in the frame.
#           Switch to detecting.
#    b. The tracker succeeds in tracking. Check if the tracked train is stationary.
#       i. If train is stationary, add it to the stationary_trains list
#       ii. Else, continue tracking train
def loop(STREAM, ENGINE, DEBUG, MySQLF, EMPTY_FRAMES, tracker, CONF):
	TRACKER = OPENCV_OBJECT_TRACKERS[tracker]()
	CONF = CONF/100
	tracking = False
	empty_frames = 0
	BOX = [0,0,0,0]
	dist_detect_to_statioanry = 5.0
	stationary_centroids = []
	train_detect = None
	while STREAM.isOpened():
		fps = get_fps()
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		# print('fps = ' + str(fps))
		_, image = STREAM.read()
		train_detects = []
		if not tracking:
			#print('detecting')
			detections = ENGINE.detect_with_image(Image.fromarray(image), top_k=10, keep_aspect_ratio=True, relative_coord=False)
			train_detects = [d for d in detections if d.label_id == 6 and d.score >= CONF]
			if len(train_detects) == 0:
				continue
			arr = np.array([d.bounding_box for d in train_detects])
			print(arr)
			train_centroids = arr.sum(axis=1) / 2
			# now calculate distances between each pair of input trains and stationary trains
			if len(stationary_centroids) > 0:
				D = dist.cdist(np.array(stationary_centroids), train_centroids)
				mins = np.amin(D, axis=1)
				cols = [np.where(D[i] == mins[i])[0][0] for i in range(mins.shape[0])]
				min_heap = [(mins[row], (row,col)) for row,col in enumerate(cols)] # creating list of nested tuple - (min_value, (row,col))
				heapq.heapify(min_heap)
				used_cols = set()
				renew_stationary = []
				while(min_heap[0][0] <= dist_detect_to_statioanry):
					(min_value,(row,col)) = heapq.heappop(min_heap)
					if not col in used_cols:
						used_cols.add(col)
					else:
						continue
					renew_stationary.append(stationary_centroids[row])
					del train_detects[col]
				stationary_centroids = renew_stationary
				print('discounted stationary_trains, #train_detects = ' + str(len(train_detects)))
			if len(train_detects) > 0: # is a train event
				initBB = train_detects[0].bounding_box.flatten().astype("int")
				initBB = tuple(initBB)
				BOX = initBB
				(x0,_,x1,_) = initBB
				# if(x1-x0>=100):
				TRACKER = OPENCV_OBJECT_TRACKERS[tracker]()
				train_detect = train_detects[0]
				del train_detects[0]
				train_detect.bounding_box = BOX
				TRACKER.init(image, initBB)
				tracking = True
			else:
				print('not tracking')
		else:
			(success, box) = TRACKER.update(image)
			if success: # continue train event
				hDist = ydist(BOX,box)
				if hDist < 1:
					# train is stationary, add to stationary_trains list
					stationary_centroids.append(box2centroid(box))
					tracking = False
					empty_frames = 0
				else:
					train
					BOX = box
					train_detect.bounding_box = BOX
					empty_frames = 0
			elif empty_frames >= EMPTY_FRAMES: # end train event
				tracking = False
			else:
				empty_frames += 1
		if DEBUG:
			#for detect in detections:
			#debug(train_detects, BOX, fps, image, timestamp, tracking)
			#debug(detect, detect.bounding_box.flatten().astype("int"), fps, image, timestamp)
			debug_multi(train_detects, train_detect, stationary_centroids, FPS, IMAGE)



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
	PARSER.add_argument('-o', '--output_path', action='store', default='/home/coal/Desktop/output/', help="Path to output directory.")
	PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
	PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
	PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")
	PARSER.add_argument('-M', '--mysql_frequency', action='store', type=int, default=100, help="Number of records in writeback to MySQL")
	PARSER.add_argument('-E', '--empty_frames', action='store', type=int, default=50, help="Length of empty frame buffer.")
	PARSER.add_argument('-C', '--collect_frequency', action='store', type=int, default=10, help="Collect 1 image in collect_frequency.")
	PARSER.add_argument('-t', '--tracker', action='store', type=str, default="kcf", help="OpenCV object tracker type")
	PARSER.add_argument('-conf', '--confidence', action='store', type=int, default=30, help="Detection confidence level out of 100.")
	PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")

	ARGS = PARSER.parse_args()
	COLLECT_FREQUENCY = ARGS.collect_frequency
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

	#global OPENCV_OBJECT_TRACKERS
	OPENCV_OBJECT_TRACKERS = {
		"csrt": cv2.TrackerCSRT_create,
		"kcf": cv2.TrackerKCF_create,
		"boosting": cv2.TrackerBoosting_create,
		"mil": cv2.TrackerMIL_create,
		"tld": cv2.TrackerTLD_create,
		"medianflow": cv2.TrackerMedianFlow_create,
		"mosse": cv2.TrackerMOSSE_create
	}

	# grab the appropriate object tracker using our dictionary of
	# OpenCV object tracker objects
	#TRACKER = OPENCV_OBJECT_TRACKERS[ARGS.tracker]()

	try:
		if not STREAM.isOpened():
			STREAM.open()
		loop(STREAM, ENGINE, ARGS.debug, ARGS.mysql_frequency, ARGS.empty_frames, ARGS.tracker, ARGS.confidence)
		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()








	