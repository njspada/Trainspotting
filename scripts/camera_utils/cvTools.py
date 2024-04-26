import imutils
import cv2
from PIL import Image

from edgetpu.classification.engine import ClassificationEngine
from edgetpu.utils import dataset_utils

# Specify model
modelPath = "/home/trainspotting/scripts/camera_utils/"
model = modelPath + "mobilenet_v2_1.0_300_quant_edgetpu.tflite"
labelPath = modelPath + "image_labels.txt"
print("[INFO] loading Coral model...")
model = ClassificationEngine(model)

imageSize = 300

# Specify the confidence required
conf = 0.50 # boo, trains are hard I guess

def read_labels(labelPath):
    # print("[INFO] parsing class labels...")
    labels=[]
    for row in open(labelPath):
        labels.append(row.strip().split("\n")[0])
    
    return labels


def prepare_frame(image):
    # Resize image to fit TFLite model
    frame = imutils.resize(image, height = imageSize, width = imageSize)

    # prepare the frame for object detection by converting it from
    # 1) BGR to RGB channel ordering and then
    # 2) from a NumPy array to PIL image format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)

    return frame


def detect_trains(image, labels):
    image = prepare_frame(image)

    # Run image through TFLite model to determine if a train is present
    results = model.classify_with_image(image, top_k=1)

    if results:
        classID = labels[results[0][0]]
        score = round(float(results[0][1])*100, 2)
        if score >= conf:
            return classID, score;
        else:
            return None
    else:
        return None
