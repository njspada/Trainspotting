import argparse
import configparser
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
import cv2
import numpy as np
import time


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

def loop(STREAM, ENGINE, T, CONF):
	detected = []
	startTime = time.time()
	CONF /= 100
	while time.time() - startTime <= T:
		_, image = STREAM.read()
		detections = ENGINE.detect_with_image(Image.fromarray(image), threshold=CONF, top_k=10, keep_aspect_ratio=True, relative_coord=False)
		train_detects = [d for d in detections if d.label_id == 6]
		detected.append(len(train_detects))
		cv2.imshow('Trainspotting', image)
		keyCode = cv2.waitKey(1) & 0xFF
		# Stop the program on the 'q' key
		if keyCode == ord("q"):
			break
	return detected

def acc(d, n=1):
	return (len([t for t in d if t >= n])/len(d))

def zero_stats(d):
	consec_zeros = []
	c = 0
	while len(d) > 0:
		i = d.pop()
		if i == 0:
			c += 1
		elif c > 0:
			consec_zeros.insert(0,c)
			c = 0
	return consec_zeros
#if __name__ == "__main__":
def run_test(t=10,conf=30):
	
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
		return (loop(STREAM, ENGINE, t, conf))

		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()