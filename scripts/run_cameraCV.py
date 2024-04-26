import cv2
import time
from datetime import datetime
from config import camera_config

from camera_utils import gstreamer
from camera_utils import cvTools
from camera_utils.keyClipWriter import KeyClipWriter


def loop(STREAM, kcw, labels, ARGS):
	# Initialize end frames counter
	endFrames = 0
	time.sleep(2.0)

	while STREAM.isOpened():

		# Catch frame from camera, prepare for model, and detect
		_,img = STREAM.read()
		results = cvTools.detect_trains(img, labels)
		updateEndFrames = True

		if results:
			t = datetime.datetime.now()
			text = f'{t.strftime("%Y-%m-%d %H:%M:%S")}, {results[0]}, {results[1]} %'

			cv2.putText(
				img, text, (10, 20),
				fontFace = cv2.FONT_HERSHEY_COMPLEX,
				fontScale = 0.5, color = (250, 225, 100)
			)

			updateEndFrames = False
			endFrames = 0

			# If we're not already recording, start
			if not kcw.recording:
				date = t.strftime('%Y-%m-%d')
				hour = t.strftime('%H')
				stamp = int(t.timestamp())
				p = f"{ARGS.outputpath}{date}/{hour}/{stamp}.avi"
				kcw.start(p, cv2.VideoWriter_fourcc(*'MJPG'), 10)
			
			if updateEndFrames:
				endFrames += 1
			
			# Update the key frame clip buffer
			kcw.update(img)

			# If we are recording and reached a threshold on
			# consecutive number of frames with no trains, stop
			if kcw.recording and endFrames == bufferSize:
				kcw.finish()

if __name__ == "__main__":
	labels = cvTools.read_labels(cvTools.labelPath)
	# print(labels)
	try:
		# load config arguments
		ARGS = camera_config.ARGS
		bufferSize = ARGS.fps * 5
		# Setup image capture stream
		STREAM = cv2.VideoCapture(gstreamer.pipeline(ARGS), cv2.CAP_GSTREAMER)
		# Initialize KeyClipWriter
		kcw = KeyClipWriter(bufSize = bufferSize)
		if not STREAM.isOpened():
			STREAM.open()
		try:
			loop(STREAM,kcw,labels,ARGS)
		except KeyboardInterrupt:
			if kcw.recording():
				kcw.finish()
			STREAM.release()
	except Exception as e:
		print(e)
		print('Exiting')
	cv2.destroyAllWindows()