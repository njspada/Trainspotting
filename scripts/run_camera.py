import cv2
import time
from config import camera_config
import local_database_connector as database_config

from camera_utils import logger
from camera_utils import gstreamer

def loop(STREAM, ARGS):
	collect_delta = ARGS.collect_delta
	end_t = time.time() + collect_delta
	while STREAM.isOpened():
		if time.time() >= end_t:
			print('inside')
			_,img = STREAM.read()
			logger.save_frame(image=img,args=ARGS,cnx=database_config)
			print('outside')
			end_t = time.time() + collect_delta

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








