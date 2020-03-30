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


# specify models etc.
modelPath = "/usr/local/controller/tools/edgetpu_models/"
model = modelPath + "mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
print("[INFO] loading Coral model...")
model = DetectionEngine(model)


# initialize the labels dictionary
print("[INFO] parsing class labels...")
labels = {}
 
# loop over the class labels file
for row in open(modelPath + "coco_labels.txt"):
	# unpack the row and update the labels dictionary
	(classID, label) = row.strip().split(maxsplit=1)
	labels[int(classID)] = label.strip()

# create lists of objects of interest
vehicles = range(1,9)

detectionStart = ""
detectionEnd = ""
detectList = []

# Specify paths
outputPath = "/mnt/p1/output/"
logPath = outputPath + "camera_"
imgPath = outputPath + "images/"

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

def save_image(image_path, timestamp, image):
    cv2.imwrite(image_path + timestamp + '.jpg', image)

def get_timestamp_iso():
    return datetime.now().isoformat()

def get_image_from_camera(video_capture):
    _, frame = cap.read()
    frame = imutils.resize(frame, height = 300, width=300) #check if this is necessary
    # prepare the frame for object detection by converting it from
    # 1) BGR to RGB channel ordering and then
    # 2) from a NumPy array to PIL image format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)
    return frame

#def save_detect(image_file_path, timestamp, image, results):

def log_detect_list(log_file_name, detect_list, detection_start, detection_end):
    entry = ['_'.join(detect_list), detection_start, detection_end]
    record = '.'.join(entry) + '\n'
    record = record + "\n"
    with open(log_file_name, 'a') as the_file:
        the_file.write(record)

def train_detect():
    detects = 0 # keep track of train detection frames
    nondetects = 0 # keep track of frames without trains, check for false negatives
    FPS = 120
    detect_interval = FPS * 3
    nondetect_threshold_interval = FPS * 60 * 30
    required_confidence = 0.35 # boo, trains are hard I guess
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if not cap.isOpened(): print("Unable to open camera.")
    while cap.isOpened():
        timeStamp = get_timestamp_iso()
        frame = get_image_from_camera(cap)
        # make predictions on the input frame
        results = model.DetectWithImage(frame, threshold=required_confidence,
                                        keep_aspect_ratio=True,
                                        relative_coord=False)
        if any(r.label_id in vehicles for r in results):
            # Vehicle has been detected
            detectionStart = timeStamp if detects == 0 else detectionStart
            if detects % detect_interval == 0:
                save_image(imgPath + 'detect_', timeStamp, img)
            detects += 1
            nondetects = 0
        else: # No vehicles detected
            nondetects += 1
            if detects > 0:
                fname = logPath + NOW.strftime("%Y-%m-%d") + ".log"
                log_detect_list(fname, detectList, detectionStart, timeStamp)
                # Clear detection list and reset counter
                detectList = []
                detects = 0
            if nondetects == nondetect_threshold_interval:
                save_image(imgPath + 'nondetect_', timeStamp, img)
                nondetects = 0        
        keyCode = cv2.waitKey(1) & 0xFF
        if keyCode == ord("q"): break 
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    train_detect()
