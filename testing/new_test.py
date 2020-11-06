def loop0(stream,engine):
	from PIL import Image
	_,img = stream.read()
	return engine.classify_with_image(Image.fromarray(img))

def loop1(maxlen,model):
	import cv2
	from edgetpu.classification.engine import ClassificationEngine as ce
	engine = ce(model)
	from config import camera_config as c
	from camera_utils import gstreamer as g
	stream = cv2.VideoCapture(g.pipeline(c.ARGS), cv2.CAP_GSTREAMER)
	sum = 0
	d = []
	while cv2.waitKey(33) != ord('q'):
		preds = loop(stream,engine)
		can = preds[0][1] if preds[0] == 1 else 1. - preds[0][1]
		if len(d) > maxlen:
			sum -= d[0]
			del d[0]
		d.append(can)
		sum += can
		print(sum/len(d))