import argparse
import configparser
import cv2
from edgetpu.detection.engine import DetectionEngine
from PIL import Image
import time
from os import makedirs

PARSER = argparse.ArgumentParser(description='Test gstreamer.')
PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
PARSER.add_argument('-cW', '--capturewidth', type=int, action='store', default=300, help="Capture Width")
PARSER.add_argument('-cH', '--captureheight', type=int, action='store', default=300, help="Capture Height")
PARSER.add_argument('-dW', '--displaywidth', type=int, action='store', default=300, help="Capture Width")
PARSER.add_argument('-dH', '--displayheight', type=int, action='store', default=300, help="Capture Height")
PARSER.add_argument('-F', '--fps', action='store', type=int, default=59, help="Capture FPS")
PARSER.add_argument('-o', '--outputpath', action='store', default='/home/dhawal/test/output/', help="Save frames here.")
ARGS = PARSER.parse_args()

def get_gstr(
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
		"video/x-raw, format=(string)BGR ! appsink max-buffers=1 drop=True"
		% (
			capture_width,
			capture_height,
			framerate,
			flip_method,
			display_width,
			display_height,
		)
	)

def get_cap():
	print('Setting up streamer!!!!')
	return cv2.VideoCapture(get_gstr(capture_width = ARGS.capturewidth, capture_height = ARGS.captureheight,
				display_width = ARGS.displaywidth, display_height = ARGS.displayheight, framerate=ARGS.fps), cv2.CAP_GSTREAMER)

def get_args():
	return ARGS

def get_dengine():
	return DetectionEngine(ARGS.model)

def save_frames(t=60,cap=get_cap(),opath=ARGS.outputpath):
	try:
		makedirs(opath)
	except:
		print('Warning path already exists!')
	end_t = time.time()+t
	i = -1
	while time.time() < end_t:
		_,img = cap.read()
		i += 1
		Image.fromarray(img).save(opath + str(i) + '.jpg')
		# cv2.imwrite(opath + str(i) + '.jpg',img)
	print(f'Collected {i} frames.')
	return i

def run_detect(t=60,e=get_dengine(),conf=0,k=10,cap=get_cap()):
	result = {}
	end_t = time.time() + t
	while time.time() < end_t:
	     _,i = cap.read()
	     detects = e.detect_with_image(Image.fromarray(i),threshold=0,top_k=10)
	     detects = [d for d in detects if d.label_id==6]
	     print(len(detects))



