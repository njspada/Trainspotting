#!/usr/bin/python3

import jetson.inference
import jetson.utils
import time
import numpy as np
import edgetpu.detection.engine
from edgetpu.utils import dataset_utils
from PIL import Image
import cv2
import imutils

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


#def capsule2img(image) -> bytes:
def capsule2img(image):
    out_arr = jetson.utils.cudaToNumpy(*image,4)
    return out_arr.tobytes()

# specify models etc.
modelPath = "/usr/share/edgetpu/examples/models/"
model = modelPath + "ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
labels = dataset_utils.ReadLabelFile(modelPath + "coco_labels.txt")
engine = edgetpu.detection.engine.DetectionEngine(model)

# create lists of objects of interest
trains = (467, 548, 566, 706, 821)
cars = (437, 469, 570, 752, 818, 867)

# create the camera and display
width, height = (1280, 720)
font = jetson.utils.cudaFont()
#camera = jetson.utils.gstCamera(width, height, "0")
#camera.Open()
cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
display = jetson.utils.glDisplay()

while display.IsOpen():

    # capture image for detections
    #img, width, height = camera.CaptureRGBA(zeroCopy=1)
    #ret, img = cap.read()
    #img_conv = capsule2img((img, width, height))
    #img_conv = Image.frombytes('RGBA', (width, height), img_conv, 'raw')
    #img_conv = img_conv.resize((300,300))

    ret, img = cap.read()
    frame = imutils.resize(img, height = 300, width=300)
    #orig = frame.copy()

    # prepare the frame for object detection by converting it from
    # 1) BGR to RGB channel ordering and then
    # 2) from a NumPy array to PIL image format
    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(cvimage)

    # run inference
    #detects = engine.detect_with_image(img_conv, top_k=3, keep_aspect_ratio=True)
    detects = engine.detect_with_image(frame, top_k=3, keep_aspect_ratio=True)
    for detect in detects:
        conf = detect.score
        if conf > 0.0:
            print('---------------------------')
            #print(detect[0])
            print(labels[detect.label_id])
            print('Score : ', conf)

    # render the image
    #display.RenderOnce(img, width, height)
    cv2.imshow('image', cvimage)
    if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # synchronize with the GPU
    if len(detects) > 0:
        jetson.utils.cudaDeviceSynchronize()

    print("----------")


camera.Close()
