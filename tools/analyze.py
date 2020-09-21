import argparse
import cv2
from edgetpu.detection.engine import DetectionEngine
import time
import readchar
from PIL import Image
import numpy as np
from skimage.measure import compare_ssim
import imutils

diff = 1

def help():
	print('h=help, q=quit, n=next, p=previous, j=jump /{num/}')


def display_image(DETECTS, IMAGE):
	def put_lines(IMAGE, BOX, LABEL, SCORE, BOX_COLOR_BGR):
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), BOX_COLOR_BGR, 5)
		(startX, startY, endX, endY) = BOX
		y = startY - 40 if startY - 40 > 40 else startY + 40
		text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)

	for d in DETECTS:
		put_lines(IMAGE, d.bounding_box.flatten().astype('int'), 'train', d.score, (0,0,255)) # moving box is red color
	# for i,box in enumerate(STAT_DETECTS.bounding_boxes):
	# 	put_lines(IMAGE, box.flatten().astype('int'), 'train', STAT_DETECTS.scores[i], (255,0,0))
	# cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)
	cv2.waitKey(20)

def get_pil_image(i):
	return Image.open(ARGS.outputpath + str(i) + '.jpg')

def get_detects(img):
	detects = engine.detect_with_image(img, threshold=ARGS.conf, top_k=10, keep_aspect_ratio=True, relative_coord=False)
	detects = [d for d in detects if d.label_id == 6]
	return detects

def show_detects(i,img):
	detects = get_detects(img)
	display_image(detects,np.array(img))

def show_diffs(i,dif):
	if i-dif < 0:
		return
	print(f"i={i}, d={dif}")
	imageA = cv2.imread(ARGS.outputpath + str(i) + '.jpg')
	imageB = cv2.imread(ARGS.outputpath + str(i-dif) + '.jpg')
	grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
	grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
	(score, diff) = compare_ssim(grayA, grayB, full=True)
	diff = (diff * 255).astype("uint8")
	print("SSIM: {}".format(score))
	thresh = cv2.threshold(diff, 0, 255,
		cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	boxes = [cv2.boundingRect(c) for c in cnts]
	for c in cnts:
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(imageA, (x, y), (x + w, y + h), (0, 0, 255), 2)
		cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)
	cv2.imshow("Original", imageA)
	cv2.imshow("Modified", imageB)
	cv2.imshow("Diff", diff)
	cv2.imshow("Thresh", thresh)
	cv2.waitKey(20)



def refresh_image(i,method,dif=1):
	# img = Image.open(ARGS.outputpath + str(i) + '.jpg')
	img = get_pil_image(i)
	if method == 'detect':
		show_detects(i,img)
	elif method == 'diff':
		show_diffs(i=i,dif=dif)

def loop(n,dif):
	if n < 1:
		print('n < 1 !!! Exiting.')
		return
	i = -1
	ch = 'n'
	while ch != 'q':
		print(ch)
		if ch == 'n':
			i = i+1 if i+1 < n else i
		elif ch == 'p':
			i = i-1 if i-1 >= 0 else i
		elif ch == 'j':
			print('Enter jump n: ')
			d = int(input())
			if i+d < n and i+d >= 0:
				i += d
			else:
				print('Cannot jump.')
		elif ch == 'k':
			print('Jump to: ')
			d = int(input())
			if d < n and d >= 0:
				i = d
			else:
				print('Cannot jump.')
		elif ch == 'd':
			print('A: ')
			a = int(input())
			print('B: ')
			b = int(input())
			if a < 0 or b < 0:
				continue
			dif = a-b if a-b >= 0 else b-a
			i = a
		else:
			help()
		refresh_image(i,method=ARGS.method,dif=dif)
		print(f'{i+1}/{n}')
		# print('Enter>')
		ch = readchar.readchar()
	cv2.destroyAllWindows()
			


# def run_detect(t=60,e=get_dengine(),conf=0,k=10,cap=get_cap()):
# 	result = {}
# 	end_t = time.time() + t
# 	while time.time() < end_t:
# 	     _,i = cap.read()
# 	     detects = e.detect_with_image(Image.fromarray(i),threshold=0,top_k=10)
# 	     detects = [d for d in detects if d.label_id==6]
# 	     print(len(detects))

if __name__ == "__main__":
	PARSER = argparse.ArgumentParser(description='Test gstreamer.')
	PARSER.add_argument('-m', '--model', action='store', default='/Users/dhawalmajithia/Desktop/works/aqi/tflite/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
	PARSER.add_argument('-me', '--method', action='store', default='detect', help="Method.")
	PARSER.add_argument('-l', '--label', action='store', default='/Users/dhawalmajithia/Desktop/works/aqi/tflite/coco_labels.txt', help="Path to labels text file.")
	PARSER.add_argument('-o', '--outputpath', action='store', default='/Users/dhawalmajithia/Desktop/works/aqi/output/', help="Save frames here.")
	PARSER.add_argument('-n', '--nimages', type=int, action='store', default=300, help="Total number of images in outputpath")
	PARSER.add_argument('-c', '--conf', type=int, action='store', default=30, help="Detect threshold")
	PARSER.add_argument('-d', '--diff', type=int, action='store', default=1, help="Image diff diff")
	ARGS = PARSER.parse_args()
	ARGS.conf = ARGS.conf/100.00
	diff=ARGS.diff
	if ARGS.method == 'detect':
		engine = DetectionEngine(ARGS.model)
	loop(n=ARGS.nimages,dif=ARGS.diff)



