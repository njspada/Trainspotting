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


def train_detect():

    # Initialize counters used for determining which frames to save
    # and keep track of events
    detects = 0 # keep track of train detection frames
    clear = 0   # keep track of frames without trains, check for false negatives
    # The intervals are dependent on the framerate. The self-reported FPS is 120
    FPS = 120
    # collect every 3 seconds at 21 FPS, check for false positives
    detectInterval = FPS * 3
    # collect 1 frame every 30 min at 21 FPS, check false neg
    clearInterval = FPS * 60 * 30
    
    detectionStart = ""
    detectionEnd = ""
    detectList = []

    # Specify paths
    outputPath = "/mnt/p1/output/"
    logPath = outputPath + "camera_"
    imgPath = outputPath + "images/"

    # Specify the confidence required
    conf = 0.35 # boo, trains are hard I guess

    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        #cv2.namedWindow("Train Detect", cv2.WINDOW_AUTOSIZE)
        while cap.isOpened():
        #while cv2.getWindowProperty("Train Detect", 0) >= 0:

            # Grab time
            NOW = datetime.now()
            timeStamp = NOW.isoformat()

            # Catch frame from camera
            ret, img = cap.read()
            frame = imutils.resize(img, height = 300, width=300)
            orig = frame.copy()

            # prepare the frame for object detection by converting it from
            # 1) BGR to RGB channel ordering and then
            # 2) from a NumPy array to PIL image format
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            
            # make predictions on the input frame
            results = model.DetectWithImage(frame, threshold=conf,
                                            keep_aspect_ratio=True,
                                            relative_coord=False)

            if any(r.label_id in vehicles for r in results):
                # Vehicle has been detected

                if detects == 0:
                    detectionStart = timeStamp
                    
                if detects % detectInterval == 0:
                    # Save frame
                    fname = imgPath + "detect_" + timeStamp + ".jpg"
                    cv2.imwrite(fname, img)

                detects += 1

                if clear > 0:
                    clear = 0

                for r in results:
                    # we only want to look at detections in our list
                    if r.label_id in vehicles:

                        # For viewing bounding box
                        box = r.bounding_box.flatten().astype("int")
                        (startX, startY, endX, endY) = box
                        label = labels[r.label_id]
                        # Add label to detect list if not already there
                        if label not in detectList:
                            detectList.append(label)

                        # draw the bounding box and label on the image
                        cv2.rectangle(orig, (startX, startY), (endX, endY),
                                      (0, 255, 0), 2)
                        y = startY - 15 if startY - 15 > 15 else startY + 15
                        text = "{}: {:.2f}%".format(label, r.score * 100)
                        cv2.putText(orig, text, (startX, y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            else:
                # No vehicles detected
                clear += 1

                if detects > 0:
                    # detection event is over
                    detectionEnd = timeStamp
                    
                    today = NOW.strftime("%Y-%m-%d")
                    fname = logPath + today + ".log"

                    # Create log entry
                    entry = ["_".join(detectList), detectionStart, detectionEnd]
                    record = ",".join(entry)
                    record = record + "\n"

                    with open(fname, "a") as the_file:
                        the_file.write(record)

                    # Clear detection list and reset counter
                    detectList = []
                    detects = 0

                if clear == clearInterval:
                    # Save frame
                    fname = imgPath + "nondetect_" + timeStamp + ".jpg"
                    cv2.imwrite(fname, img)
                    
                    # Reset counter
                    clear = 0        
                    

            # show the output frame and wait for a key press
            #cv2.imshow("Train Detect", orig)
            keyCode = cv2.waitKey(1) & 0xFF
            # Stop the program on the 'q' key
            if keyCode == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
    else:
        print("Unable to open camera")


if __name__ == "__main__":
    train_detect()
