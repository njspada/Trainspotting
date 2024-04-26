#!/usr/bin/python3

# Build up testing
# Build up the Python code needed to run the camera system
# Use 'coffee mug' for testing

from edgetpu.classification.engine import ClassificationEngine
from PIL import Image
from keyClipWriter import KeyClipWriter
import cv2
import imutils
import time
import datetime

basePath = "/usr/share/edgetpu/examples/models/"
modelPath = basePath + "mobilenet_v2_1.0_224_quant_edgetpu.tflite"
labelPath = basePath + "imagenet_labels.txt"
output = "/home/sickboy/Documents/"

frameRate = 60
bufferSize = frameRate * 5

imgSize = 224 # imagenet
#imgSize = 300 # custom model

print("[INFO] loading Coral model...\n\n")
model = ClassificationEngine(modelPath)


def readLabels(labelPath):
	print("[INFO] parsing class labels...")
	labels=[]
	for row in open(labelPath):
		labels.append(row.strip().split("\n")[0].split("  ")[1]) # imagenet
		#labels.append(row.strip().split("\n")[0]) # custom model
	
	return labels

def prepareImage(image):
	image = imutils.resize(image, height=imgSize, width=imgSize)
	image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	image = Image.fromarray(image)
	
	return image

def classifyImage(image):
	image = prepareImage(image)
	results = model.classify_with_image(image, top_k=1)
	
	if results:
		classID = labels[results[0][0]].split(", ")[0]
		score = round(float(results[0][1])*100, 2)
		return classID, score;
	else:
		return None
	
	return results
	

def gstream(
	camWidth = imgSize,
	camHeight = imgSize,
	FPS = frameRate,
	flipMode = 0,
	dispWidth = imgSize*2,
	dispHeight = imgSize*2):
	return (
		"nvarguscamerasrc ! "
		"video/x-raw(memory:NVMM), "
		"width=(int)%d, height=(int)%d, "
		"format=(string)NV12, framerate=(fraction)%d/1 ! "
		"nvvidconv flip-method=%d ! "
		"video/x-raw, width=(int)%d, height=(int)%d, "
		"format=(string)BGRx ! "
		"videoconvert ! "
		"video/x-raw, format=(string)BGR ! "
		"appsink max-buffers=1 drop=True"
		% (camWidth, camHeight, FPS, flipMode, dispWidth, dispHeight)
	)

def loop(STREAM, kcw):
	
	endFrames = 0
	time.sleep(2.0)
	
	while STREAM.isOpened():
		
		_, image = STREAM.read()
		
		results = classifyImage(image)
		updateEndFrames = True
		
		if results:
			t = datetime.datetime.now()
			text = f'{t.strftime("%Y-%m-%d %H:%M:%S")}, {results[0]}, {results[1]} %' 
			cv2.putText(
				image, text, (10, 20),
				fontFace = cv2.FONT_HERSHEY_COMPLEX,
				fontScale = 0.5, color = (250, 225, 100))
			
			# Collect video if a mug was found
			if results[0] == 'coffee mug':
				updateEndFrames = False
				endFrames = 0
				
				# If we're not already recording, start
				if not kcw.recording:
					p = "{}/{}.avi".format(output, t.strftime("%Y%m%d-%H%M%S"))
					kcw.start(p, cv2.VideoWriter_fourcc(*'MJPG'), 10)
			
			if updateEndFrames:
				endFrames += 1
			
			# Update the key frame clip buffer
			kcw.update(image)
			
			# if we are recording and reached a threshold on consecutive
			# number of frames with no action, stop recording the clip
			if kcw.recording and endFrames == bufferSize:
				kcw.finish()
		
		cv2.imshow('testing', image)
		
		keyCode = cv2.waitKey(1) & 0xFF
		if keyCode == ord("q"):
			break

if __name__ == "__main__":
	labels = readLabels(labelPath)
	print(labels)
	try:
		STREAM = cv2.VideoCapture(gstream(), cv2.CAP_GSTREAMER)
		kcw = KeyClipWriter(bufSize=bufferSize)
		if not STREAM.isOpened():
			STREAM.open()
		try:
			loop(STREAM, kcw)
		except KeyboardInterrupt:
			if kcw.recording:
				kcw.finish()
			STREAM.release()
	except Exception as e:
		print(e)
		print('Exiting')
	cv2.destroyAllWindows()

print('Complete')
