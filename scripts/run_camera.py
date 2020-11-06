import cv2
import time
from PIL import Image
from edgetpu.classification.engine import ClassificationEngine
from config import camera_config
from camera_utils import gstreamer
from camera_utils import logger

def loop(STREAM, ARGS):
	Logger = logger.Logger(ARGS)
	while STREAM.isOpened():
		_,img = STREAM.read()
		img = Image.fromarray(img)
		pred = (ENGINE.classify_with_image(img))[0]
		X = logger.LoggerInput(image=img, is_train_p=pred[1] if pred[0]==1 else 1.-pred[1])
		Logger.Input(X)

if __name__ == "__main__":
	try:
		ARGS = camera_config.ARGS
		STREAM = cv2.VideoCapture(gstreamer.pipeline(ARGS), cv2.CAP_GSTREAMER)
		ENGINE = ClassificationEngine(ARGS.model)
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








