#!/usr/bin/python3

import jetson.inference
import jetson.utils
import time
import numpy as np
import edgetpu.classification.engine
from edgetpu.utils import dataset_utils
from PIL import Image

def capsule2img(image) -> bytes:
    out_arr = jetson.utils.cudaToNumpy(*image,4)
    return out_arr.tobytes()

# specify models etc.
modelPath = "/home/nick/edgetpu_models/"
model = modelPath + "mobilenet_v2_1.0_224_quant_edgetpu.tflite"
labels = dataset_utils.ReadLabelFile(modelPath + "imagenet_labels.txt")
engine = edgetpu.classification.engine.ClassificationEngine(model)

# create lists of objects of interest
trains = (467, 548, 566, 706, 821)
cars = (437, 469, 570, 752, 818, 867)

# create the camera and display
width, height = (1280, 720)
font = jetson.utils.cudaFont()
camera = jetson.utils.gstCamera(width, height, "0")
camera.Open()
display = jetson.utils.glDisplay()

while display.IsOpen():

    # capture image for detections
    img, width, height = camera.CaptureRGBA(zeroCopy=1)
    img_conv = capsule2img((img, width, height))
    img_conv = Image.frombytes('RGBA', (width, height), img_conv, 'raw')

    # run inference
    detects = engine.ClassifyWithImage(img_conv, top_k=3)
    for detect in detects:
        conf = detect[1]
        if conf > 0.2:
            print('---------------------------')
            print(labels[detect[0]])
            print('Score : ', conf)

    # render the image
    display.RenderOnce(img, width, height)

    # synchronize with the GPU
    if len(detects) > 0:
        jetson.utils.cudaDeviceSynchronize()

    print("----------")


camera.Close()
