import cv2
from PIL import Image
import time
from config import camera_config
from camera_utils import gstreamer

def loop(STREAM):
	collect_delta = 10 # collect for 10 seconds
	end_t = time.time() + collect_delta
	while STREAM.isOpened():
		if time.time() <= end_t:
			_,img = STREAM.read()
			

if __name__ == "__main__":
	try:
		# load config arguments
		ARGS = camera_config.ARGS
		# Setup image capture stream
		STREAM = cv2.VideoCapture(gstreamer.pipeline(ARGS), cv2.CAP_GSTREAMER)
		if not STREAM.isOpened():
			STREAM.open()
		try:
			loop(STREAM,ARGS)
		except KeyboardInterrupt:
			STREAM.release()
	except Exception as e:
		print(e)
		print('Exiting')
	cv2.destroyAllWindows()