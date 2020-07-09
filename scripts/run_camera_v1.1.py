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
import threading

start_t = time.time()
frame_times = []

last_time = time.time()

DATA_ARR = []
LABELS = []

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

# for production
def write_to_db(DATA_ARR): # DATA = list{'timestamp':datetime.now(), 'conf':float, 'label': str, 'x0': int, 'y0', 'x1', 'y1', 'filename':str}
	print('writing to db')
	CNX = database_config.connection()
	if not CNX:
		print('Failed to connect to MySQL database!')
		exit()
	query = """INSERT INTO camera_detects  
				(timestamp, conf, label, `x0`, `y0`, `x1`, `y1`, filename) 
				VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""";
	try:
		cursor = CNX.cursor()
		cursor.executemany(query, DATA_ARR)
	except mysql.connector.Error as err:
		print(err)
	else:
		CNX.commit()

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

def debug(DETECT, BOX, FPS, IMAGE, TIMESTAMP):
	coords = dict(zip(['startX', 'startY', 'endX', 'endY'], BOX))
	dataline = str(TIMESTAMP) + ', ' + LABELS[DETECT.label_id] + ', conf = ' + str(DETECT.score) + ', coords = ' + str(coords) + '\n'
	print(dataline)
	display_image(IMAGE, BOX, LABELS[DETECT.label_id], DETECT.score, FPS)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		return

def save_image(IMAGE, FILENAME):
	output_path = "/home/coal/Desktop/output/"
	cv2.imwrite(output_path+FILENAME, IMAGE)
	
def store_a_train_detect(IMAGE, DETECT, LABELS, MySQLF, TIMESTAMP):
	global DATA_ARR
	global LABELS
	box = DETECT.bounding_box.flatten().astype("int")
	(startX, startY, endX, endY) = box
	filename = timestamp + '.jpg'
	DATA = [timestamp, float(DETECT.score), LABELS[DETECT.label_id], int(startX), int(startY), int(endX), int(endY), filename]
	DATA_ARR.append(DATA)
	if len(DATA_ARR) >= MySQLF:
		t = threading.Thread(target=write_to_db, args=(DATA_ARR,))
		t.start()
		DATA_ARR = []

def store_train_detects(DETECT_LIST):
	print('storing train detects')
	for i in range(0, len(DETECT_LIST)/10):
		t0 = Threading.Thread(target=store_a_train_detect, args=(*DETECT_LIST[i*10]))
		t1 = threading.Thread(target=save_image, args=(DETECT_LIST[i*10][0], DETECT_LIST[i*10][3] + 'jpg',))
		t0.start()
		t1.start()

def loop(STREAM, ENGINE, DEBUG, MySQLF):
	is_train_event = False
	detect_list = []
	while STREAM.isOpened():
		fps = get_fps()
		print('fps = ' + str(fps))
		_, image = STREAM.read()
		detections = ENGINE.detect_with_image(Image.fromarray(image), top_k=3, keep_aspect_ratio=True, relative_coord=False)
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		for detect in detections:
			if detect.label_id == 6: # 6 = train
				detect_list.append([image, detect, MySQLF, timestamp])
				if not is_train_event: # start of new train event
					print('starting new train event')
					is_train_event = True
			else:
				if is_train_event: # end of train event
					print('ending train event')
					is_train_event = False
					t = threading.Thread(target =store_train_detects, args=(detect_list,))
					t.start()
					detect_list = []
			if DEBUG:
				debug(detect, detect.bounding_box.flatten().astype("int"), fps, image, datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
	PARSER.add_argument('-o', '--output_path', action='store', default='/home/coal/Desktop/output/', help="Path to output directory.")
	PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
	PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
	PARSER.add_argument('-F', '--fps', action='store', type=int, default=20, help="Capture FPS")
	PARSER.add_argument('-M', '--mysql_frequency', action='store', type=int, default=100, help="Number of records in writeback to MySQL")
	PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")

	ARGS = PARSER.parse_args()
	# Load the DetectionEngine
	ENGINE = DetectionEngine(ARGS.model)
	if not ENGINE:
		print("Failed to load detection engine.")
		exit()
	# Read labels file
	global LABELS
	LABELS = dataset_utils.read_label_file(ARGS.label)
	if not LABELS:
		print("Failed to load labels file")
		exit()
	# Setup image capture stream
	STREAM = cv2.VideoCapture(gstreamer_pipeline(capture_width = ARGS.width, capture_height = ARGS.height, display_width = ARGS.width, display_height = ARGS.height, framerate=ARGS.fps), cv2.CAP_GSTREAMER)

	try:
		loop(STREAM, ENGINE, ARGS.debug, ARGS.mysql_frequency)
		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()








	