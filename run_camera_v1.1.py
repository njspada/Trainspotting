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

cnx = database_config.connection()
if not cnx:
	print('Failed to connect to MySQL database!')
	exit()

def gstreamer_pipeline(
	capture_width=1280,
	capture_height=720,
	display_width=1280,
	display_height=720,
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

def display_image(IMAGE, BOX, LABEL, SCORE):
	cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), (255,0,0), 5)
	(startX, startY, endX, endY) = BOX
	y = startY - 40 if startY - 40 > 40 else startY + 40
	text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
	font = cv2.FONT_HERSHEY_SIMPLEX
	cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)
	pa_data = pa.get_latest_data()
	cv2.putText(IMAGE, 'pm2.5=' + str(pa_data['pm2.5']), (20,20), font, 1, (200,255,155), 2, cv2.LINE_AA)
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


def loop(STREAM, ENGINE, LABELS, DEBUG):
	while STREAM.isOpened():
		_, image = STREAM.read()
		image = imutils.resize(image, height = 1280, width=720)
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		detect_candidate = Image.fromarray(image)
		detections = ENGINE.detect_with_image(detect_candidate, top_k=3, keep_aspect_ratio=True, relative_coord=False)
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		for detect in detections:
			box = detect.bounding_box.flatten().astype("int")
			(startX, startY, endX, endY) = box
			filename = timestamp + '.jpg'
			DATA = [timestamp, float(detect.score), LABELS[detect.label_id], int(startX), int(startY), int(endX), int(endY), filename]
			write_to_db(DATA)
			if DEBUG:
				coords = dict(zip(['startX', 'startY', 'endX', 'endY'], box))
				dataline = str(timestamp) + ', ' + LABELS[detect.label_id] + ', conf = ' + str(detect.score) + ', coords = ' + str(coords) + '\n'
				print(dataline)
				display_image(image, box, LABELS[detect.label_id], detect.score)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/local/controller/tools/edgetpu_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/local/controller/tools/edgetpu_models/coco_labels.txt', help="Path to labels text file.")
	PARSER.add_argument('-o', '--output_dir', action='store', default='output/', help="Path to output directory.")
	PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")
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
	STREAM = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
	try:
		loop(STREAM, ENGINE, LABELS, ARGS.debug)
	except KeyboardInterrupt:
		print("Program killed")








	