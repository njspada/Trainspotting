import argparse
import configparser
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import cv2
import imutils
import numpy
from datetime import datetime
import database_config
import mysql.connector
from mysql.connector import errorcode
import purple_air_sql as pa
import met_sql as met

import time

import jetson.inference
import jetson.utils

cnx = database_config.connection()
if not cnx:
	print('Failed to connect to MySQL database!')
	exit()

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

def display_image(IMAGE, BOX, LABEL, SCORE, FPS):
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
	cv2.imshow('image', IMAGE)



def write_to_db(DATA): # DATA = list{'timestamp':datetime.now(), 'conf':float, 'label': str, 'x0': int, 'y0', 'x1', 'y1', 'filename':str}
	query = """INSERT INTO camera_detects  
				(timestamp, conf, label, `x0`, `y0`, `x1`, `y1`, filename) 
				VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""";
	try:
		cursor = cnx.cursor()
		cursor.execute(query, DATA)
	except mysql.connector.Error as err:
		print(err)
	else:
		cnx.commit()


def loop_jetson(STREAM, ENGINE, LABELS, DEBUG):
	start_t = time.time()
	while True:
		start_t = time.time()
		# capture the image
		image, width, height = STREAM.CaptureRGBA(zeroCopy=True)
		jetson.utils.cudaDeviceSynchronize ()
		image = jetson.utils.cudaToNumpy (image, width, height, 4)
		image = imutils.resize(image, height = 300, width=300)
		print(aimage)
		break
		exit()
		aimage = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
		detect_candidate = Image.fromarray(aimage)
		detections = ENGINE.detect_with_image(detect_candidate, top_k=3, keep_aspect_ratio=True, relative_coord=False)
		print(str(len(detections)) + ' detects')
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		for detect in detections:
			box = detect.bounding_box.flatten().astype("int")
			(startX, startY, endX, endY) = box
			filename = timestamp + '.jpg'
			DATA = [timestamp, float(detect.score), LABELS[detect.label_id], int(startX), int(startY), int(endX), int(endY), filename]
			write_to_db(DATA)
			if DEBUG:
				end_t = time.time()
				time_taken = end_t - start_t
				start_t = end_t
				frame_times.append(time_taken)
				frame_times = frame_times[-20:]
				fps = len(frame_times) / sum(frame_times)
				coords = dict(zip(['startX', 'startY', 'endX', 'endY'], box))
				dataline = str(timestamp) + ', ' + LABELS[detect.label_id] + ', conf = ' + str(detect.score) + ', coords = ' + str(coords) + '\n'
				print(dataline)
				display_image(image, box, LABELS[detect.label_id], detect.score, fps)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break


def loop(STREAM, ENGINE, LABELS, DEBUG):
	frame_times = []
	while STREAM.isOpened():
		start_t = time.time()
		#game loop begins here

		# run logic here
		_, image = STREAM.read()
		#image = imutils.resize(image, height = 300, width=300)
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		detect_candidate = Image.fromarray(image)
		print(image)
		break
		exit()
		detections = ENGINE.detect_with_image(detect_candidate, top_k=3, keep_aspect_ratio=True, relative_coord=False)
		print(str(len(detections)) + ' detects')
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		for detect in detections:
			box = detect.bounding_box.flatten().astype("int")
			(startX, startY, endX, endY) = box
			filename = timestamp + '.jpg'
			DATA = [timestamp, float(detect.score), LABELS[detect.label_id], int(startX), int(startY), int(endX), int(endY), filename]
			write_to_db(DATA)
			if DEBUG:
				end_t = time.time()
				time_taken = end_t - start_t
				start_t = end_t
				frame_times.append(time_taken)
				frame_times = frame_times[-20:]
				fps = len(frame_times) / sum(frame_times)
				coords = dict(zip(['startX', 'startY', 'endX', 'endY'], box))
				dataline = str(timestamp) + ', ' + LABELS[detect.label_id] + ', conf = ' + str(detect.score) + ', coords = ' + str(coords) + '\n'
				print(dataline)
				display_image(image, box, LABELS[detect.label_id], detect.score, fps)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/local/controller/tools/edgetpu_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/local/controller/tools/edgetpu_models/coco_labels.txt', help="Path to labels text file.")
	#PARSER.add_argument('-o', '--output_dir', action='store', default='output/', help="Path to output directory.")
	PARSER.add_argument('-W', '--width', action='store', default=300, help="Capture Width")
	PARSER.add_argument('-H', '--height', action='store', default=300, help="Capture Height")
	PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")
	PARSER.add_argument('-j', '--jetsonutils', action='store_true', default=False, help="Use jetson utils")
	ARGS = PARSER.parse_args()
	ARGS.width = int(ARGS.width)
	ARGS.height = int(ARGS.height)
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
	STREAM = 0
	if not ARGS.jetsonutils:
		STREAM = cv2.VideoCapture(gstreamer_pipeline(capture_width = ARGS.width, capture_height = ARGS.height, display_width = ARGS.width, display_height = ARGS.height), cv2.CAP_GSTREAMER)
	else:
		STREAM = jetson.utils.gstCamera(1280, 720, "0")
	# create the camera and display
	# FONT = jetson.utils.cudaFont()
	# STREAM = jetson.utils.gstCamera(1280, 720, "0")
	# DISPLAY = jetson.utils.glDisplay()

	try:
		# loop_jetson(STREAM, ENGINE, LABELS, ARGS.debug)
		if ARGS.jetsonutils:
			loop_jetson(STREAM, ENGINE, LABELS, ARGS.debug)
		else:
			loop(STREAM, ENGINE, LABELS, ARGS.debug)
	except KeyboardInterrupt:
		print("Program killed")








	