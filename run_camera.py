# MIT License
# Copyright (c) 2019 JetsonHacks
# See LICENSE for OpenCV license and additional information

# https://docs.opencv.org/3.3.1/d7/d8b/tutorial_py_face_detection.html
# On the Jetson Nano, OpenCV comes preinstalled
# Data files are in /usr/sharc/OpenCV
import numpy as np
import cv2
import time
from datetime import datetime
import imutils
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
import sys


# specify models etc.
model_path = "/usr/local/controller/tools/edgetpu_models/"
model = model_path + "mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
print("[INFO] loading Coral model...")
model = DetectionEngine(model)


# initialize the labels dictionary
print("[INFO] parsing class labels...")
labels = {}
 
# loop over the class labels file
for row in open(model_path + "coco_labels.txt"):
	# unpack the row and update the labels dictionary
	(classID, label) = row.strip().split(maxsplit=1)
	labels[int(classID)] = label.strip()

# create lists of objects of interest
vehicles = range(1,9)

FPS = 120
detect_interval_threshold = FPS * 3
nondetect_interval_threshold = FPS * 60 * 30
required_confidence = 0.35 # boo, trains are hard I guess

# Specify paths
#output_path = "/mnt/p1/output/"
if(len(sys.argv) == 1):
    print("Provide output path!")
    exit()
output_path = sys.argv[1]
log_path = output_path + "logs/"
img_path = output_path + "images/"

# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Defaults to 1280x720 @ 30fps
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of the window on the screen
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

def save_image(image_path, time_stamp, image):
    cv2.imwrite(image_path + time_stamp + '.jpg', image)

def get_time_stamp_ymd():
	now = datetime.now()
	return now.isoformat(), now.strftime("%Y-%m-%d")

def get_image_from_camera(video_capture):
    _, frame = cap.read()
    frame = imutils.resize(frame, height = 300, width=300) #check if this is necessary
    # prepare the frame for object detection by converting it from
    # 1) BGR to RGB channel ordering and then
    # 2) from a NumPy array to PIL image format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)
    return frame

def log(now_ymd, time_stamp, results, image): # now_ymd = datetime.NOW().strftime("%Y-%m-%d")
	save_image(img_path + now_ymd + '/', time_stamp, image)
	with open(log_path + now_ymd + '.log', 'a') as log_file:
		log_file.write(time_stamp + '\n')
		for result in results:
			result = result.label_id + ' ' + ' '.join([value for value in result
				.bounding_box.flatten().astype("int")])
			log_file.write(result + '\n')

def train_detect():
    detects = 0 # keep track of train detection frames
    nondetects = 0 # keep track of frames without trains, check for false negatives
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if not cap.isOpened(): print("Unable to open camera.")
    while cap.isOpened():
        time_stamp, now_ymd = get_time_stamp_ymd()
        image = get_image_from_camera(cap)
        results = model.DetectWithImage(frame, threshold=required_confidence,
                                        keep_aspect_ratio=True,
                                        relative_coord=False)
        if any(r.label_id in vehicles for r in results):
            # Vehicle has been detected
            if detects == detect_interval_threshold:
                log(now_ymd, time_stamp, results, image)
                detects = 0
            detects += 1
            nondetects = 0
        else: # No vehicles detected
            nondetects += 1
            detects = 0
            if nondetects == nondetect_interval_threshold:
                log(now_ymd, time_stamp, [], image)
                nondetects = 0        
        keyCode = cv2.waitKey(1) & 0xFF
        if keyCode == ord("q"): break 
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    train_detect()
