import argparse
import configparser
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
import cv2
import numpy as np

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

def display_image(IMAGE, detects):
	for d in detects:
		BOX = d.bounding_box.flatten().astype(int).tolist()
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), (0,0,255), 5)
		(startX, startY, endX, endY) = BOX
		y = startY - 40 if startY - 40 > 40 else startY + 40
		text = "{}: {:.2f}%".format('train', d.score * 100)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)
		cv2.imshow('testing', IMAGE)

def loop(STREAM, ENGINE, CONF):
	CONF /= 100
	n = 0
	frames = 0
	while STREAM.isOpened():
		print(str(frames))
		frames += 1
		_, image = STREAM.read()
		detections = ENGINE.detect_with_image(Image.fromarray(image), threshold=CONF, top_k=10, keep_aspect_ratio=True, relative_coord=False)
		train_detects = [d for d in detections if d.label_id == 6]
		if len(train_detects) > 0: 
			n += 1
		display_image(image, train_detects)
		keyCode = cv2.waitKey(1) & 0xFF
		# Stop the program on the 'q' key
		if keyCode == ord("q"):
			break
	# return detected
	return n,frames

def run_test(conf=30):
	
	model = '/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite'
	label= '/usr/share/edgetpu/examples/models/coco_labels.txt'
	width = 300
	height = 300
	fps = 60

	# Load the DetectionEngine
	ENGINE = DetectionEngine(model)
	if not ENGINE:
		print("Failed to load detection engine.")
		exit()
	# Read labels file
	LABELS = dataset_utils.read_label_file(label)
	if not LABELS:
		print("Failed to load labels file")
		exit()
	# Setup image capture stream
	STREAM = cv2.VideoCapture(gstreamer_pipeline(capture_width = width, capture_height = height, display_width = width, display_height = height, framerate=fps), cv2.CAP_GSTREAMER)

	try:
		if not STREAM.isOpened():
			STREAM.open()
		return (loop(STREAM, ENGINE, conf))

		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()