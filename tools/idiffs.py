# import the necessary packages
from skimage.measure import compare_ssim
import argparse
import imutils
import cv2
import time
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--start", required=True,type=int,help="image start range")
ap.add_argument("-e", "--end", required=True,type=int,
	help="image end range")
ap.add_argument("-o", "--o", required=True,default="outputs/",help="images output path")
args = vars(ap.parse_args())

def get_score(A,B):
	# load the two input images
	imageA = cv2.imread(A)
	imageB = cv2.imread(B)
	# convert the images to grayscale
	grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
	grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
	
	# compute the Structural Similarity Index (SSIM) between the two
	# images, ensuring that the difference image is returned
	(score, _) = compare_ssim(grayA, grayB, full=True)
	return score

start = args['start'] + 1
end = args['end']
o = args['o']
with open('ssims.csv','w') as f:
	f.write('A,B,score\n')
	while start < end:
		score = get_score(o+str(start-1)+'.jpg',o+str(start)+'.jpg')
		f.write(f'{start-1},{start},{score}\n')
		start += 1
