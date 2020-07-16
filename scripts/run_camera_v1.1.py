import argparse
import configparser
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
import cv2
import numpy
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
	# pa_data = pa.get_latest_data()
	# cv2.putText(IMAGE, 'pm2.5=' + str(pa_data['pm2.5']), (20,20), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# met_data = met.get_latest_data()
	# cv2.putText(IMAGE, 'windGust=' + str(met_data['windGust']) + 'mph', (20,40), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
	# cv2.putText(IMAGE, 'wgDir=' + str(met_data['windGustDir'] if met_data['windGustDir'] else 'null'), (20,60), font, 0.5, (200,255,155), 2, cv2.LINE_AA)
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

def loop(STREAM, ENGINE, DEBUG, MySQLF, EMPTY_FRAMES, TRACKER, CONF):
	# print('empty trains = ' + str(EMPTY_FRAMES))
	CONF = CONF/100
	tracking = False # true when using tracker instead of detection engine
	was_train_event = False
	detect_list = []
	track_list = []
	empty_frames = 0
	train_detect = {}
	BOX = [0,0,0,0]
	stationary_centroids = []
	# initialize the bounding box coordinates of the train we are going to track
	initBB = None
	while STREAM.isOpened():
		fps = get_fps()
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		# print('fps = ' + str(fps))
		_, image = STREAM.read()
		if tracking:
			#print('tracking')
			(success, box) = TRACKER.update(image)
			if success: # continue train event
				track_list.append([image, box, timestamp])
				# print('tracked box = ' + str(box))
				hDist = ydist(BOX,box)
				if hDist < 1:
					# train is stationary, add to stationary_trains list
					#stationary_trains.append(box)
					stationary_centroids.append(box2centroid(box))
					tracking = False
					print('train is stationary. stopping tracking')
					empty_frames = 0
				#print('y pixels traveled = ' + str(hDist))
				else:
					BOX = box
					empty_frames = 0
			elif empty_frames >= EMPTY_FRAMES: # end train event
				tracking = False
				print('ending train event')
			else:
				empty_frames += 1
		else:
			#print('detecting')
			detections = ENGINE.detect_with_image(Image.fromarray(image), top_k=3, keep_aspect_ratio=True, relative_coord=False)
			train_detects = [d for d in detections if d.label_id == 6 and d.score >= CONF]
			train_centroids = [box2centroid(d.bounding_box.flatten()) for d in train_detects]
			if len(stationary_centroids) > 0:
				temp = []
				i = 0
				for t in train_detects:
					dx = ydist(train_centroids[i],stationary_centroids[-1])
					print('dx = ' + str(dx))
					if dx > 10:
						temp.append(t)
				train_detects = temp
				#train_detects = [d for d in train_detects if ydist(d.bounding_box.flatten().astype("int"),stationary_trains[-1]) > 1]
			if len(train_detects) > 0: # is a train event
				#detect_list.append([image, train_detects[0], timestamp])
				# detected a train, start tracking it!
				initBB = train_detects[0].bounding_box.flatten().astype("int")
				initBB = tuple(initBB)
				(x0,_,x1,_) = initBB
				if(x1-x0>=100):
					TRACKER = cv2.TrackerCSRT_create()
					train_detect = train_detects[0]
					# print('detected box = ' + str(initBB))
					BOX = initBB
					TRACKER.init(image, initBB)
					tracking = True
					print('starting train event')
			else:
				train_detect = {}
		if DEBUG:
			#for detect in detections:
			#if tracking:
			#print(train_detect)
			if train_detect != {}:
				debug(train_detect, BOX, fps, image, timestamp, tracking)
			#debug(detect, detect.bounding_box.flatten().astype("int"), fps, image, timestamp)



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
	TRACKER = OPENCV_OBJECT_TRACKERS[ARGS.tracker]()

	try:
		if not STREAM.isOpened():
			STREAM.open()
		loop(STREAM, ENGINE, ARGS.debug, ARGS.mysql_frequency, ARGS.empty_frames, TRACKER, ARGS.confidence)
		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()








	