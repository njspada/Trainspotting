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

def gstreamer_pipeline(
	capture_width=1280,
	capture_height=720,
	display_width=800,
	display_height=600,
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
	draw = ImageDraw.Draw(IMAGE)
	draw.rectangle(BOX, outline='red', width = 5)
	(startX, startY, endX, endY) = box
	y = startY - 40 if startY - 40 > 40 else startY + 40
	text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
	fnt = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 40)
	#font = ImageFont.truetype("sans-serif.ttf", 16)
	draw.text((startX,y), text, font=fnt, fill=(0, 255, 0))
	cv2.imshow('image', IMAGE)

def loop(STREAM, ENGINE, LABELS, DEBUG):
	while STREAM.isOpened():
		_, image = STREAM.read()
		image = imutils.resize(image, height = 300, width=300)
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		detect_candidate = Image.fromarray(image)
		detections = ENGINE.detect_with_image(detect_candidate, top_k=3, keep_aspect_ratio=True, relative_coord=False)
		timestamp = datetime.now().isoformat()
		for detect in detections:
			box = detect.bounding_box.flatten().tolist()
			coords = dict(zip(['startX', 'startY', 'endX', 'endY'], box))
			dataline = str(timestamp) + ', ' + LABELS[detect.label_id] + ', conf = ' + str(detect.score) + ', coords = ' + str(coords) + '\n'
			print(dataline) # here we insert into database
			if DEBUG:
				display_image(detect_candidate, box, LABELS[detect.label_id], detect.score)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break



if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Run detection on trains.')
	PARSER.add_argument('-m', '--model', action='store', default='/usr/local/controller/tools/edgetpu_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-l', '--label', action='store', default='/usr/local/controller/tools/edgetpu_models/coco_labels.txt', help="Path to labels text file. Default")
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








	