from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
import time
import heapq
from scipy.spatial import distance as dist

from config import camera_config
import local_database_connector as database_config
from camera_utils import trains
from camera_utils import train_logger
# from camera_utils import debug_logger

# for fps calculations
start_t = time.time()
frame_times = []
last_time = time.time()

LABELS = []

def gstreamer_pipeline(
	capture_width=300,
	capture_height=300,
	display_width=300,
	display_height=300,
	framerate=21,
	flip_method=0,
	):
	return (
		"nvarguscamerasrc ! "
		"video/x-raw(memory:NVMM), "
		"width=(int)%d, height=(int)%d, "
		"format=(string)NV12, framerate=(fraction)%d/1 ! "
		"nvvidconv flip-method=%d ! "
		"video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
		"videoconvert ! "
		"video/x-raw, format=(string)BGR ! appsink max-buffers=1 drop=True"
		% (
			capture_width,
			capture_height,
			framerate,
			flip_method,
			display_width,
			display_height,
		)
	)

# for debugging
def get_fps() -> float: # returns (fps,start_t)
	global frame_times
	global start_t
	end_t = time.time()
	time_taken = end_t - start_t
	frame_times.append(time_taken)
	frame_times = frame_times[-20:]
	fps = 20 / sum(frame_times)
	start_t = time.time()
	return fps

def debug_mul(MOVING_DETECTS, STAT_DETECTS, IMAGE, FPS):
	def put_lines(IMAGE, BOX, LABEL, SCORE, BOX_COLOR_BGR):
		cv2.rectangle(IMAGE, (BOX[0],BOX[1]), (BOX[2],BOX[3]), BOX_COLOR_BGR, 5)
		(startX, startY, endX, endY) = BOX
		y = startY - 40 if startY - 40 > 40 else startY + 40
		text = "{}: {:.2f}%".format(LABEL, SCORE * 100)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(IMAGE, text, (startX, y), font, 1, (200,255,155), 2, cv2.LINE_AA)

	for i,box in enumerate(MOVING_DETECTS.bounding_boxes):
		put_lines(IMAGE, box.flatten().astype('int'), 'train', MOVING_DETECTS.scores[i], (0,0,255)) # moving box is red color
	for i,box in enumerate(STAT_DETECTS.bounding_boxes):
		put_lines(IMAGE, box.flatten().astype('int'), 'train', STAT_DETECTS.scores[i], (255,0,0))
	cv2.putText(IMAGE, 'fps=' + str(FPS), (20,240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,255,155), 2, cv2.LINE_AA)
	cv2.imshow('Trainspotting', IMAGE)

def match_min_dist(row_vector, col_vector, dist_limit):
	# row_vector and col_vector are numpy arrays of points.
	# dist.cdist calculates euclidean distance between each
	# pair of points in row and col and returns a m*n matirx.
	# m = len(row_vector), n = len(col_vector)
	D = dist.cdist(row_vector, col_vector)
	# amin(D, axis=1) returns a column vector with minimum values of each row
	mins = np.amin(D, axis=1)
	# we want the indices of the columns in which the row-minimums occur
	cols = [np.where(D[i] == mins[i])[0][0] for i in range(mins.shape[0])]
	# create a list of nested tuples 
	min_heap = [(mins[row], (row,col)) for row,col in enumerate(cols)] # creating list of nested tuple - (min_value, (row,col))
	# sort the tuples using a minheap, sorting by distance ascending
	heapq.heapify(min_heap)
	# keep track of matched pairs because we want them to be unique! (unique row,unique col)
	used_cols = set()
	used_rows = []
	while len(min_heap) > 0:
		(min_value,(row,col)) = heapq.heappop(min_heap)
		if min_value < dist_limit:
			# we only check for col in used_cols because rows are already unique, we made a column vector for min cols in each row.
			if col not in used_cols:
				used_cols.add(col)
				used_rows.append(row)
			else:
				continue
	return (used_rows, used_cols)


def loop(STREAM, ENGINE, DEBUG, CONF, DTS, DDS, EFT, EFD, DFPS, ARGS):
	CONF = CONF/100
	stationary_centroids = [[],[]] # [centroid][consecutive empty frames]
	previous_centroids = [[],[]]

	stationary_trains = trains.trains()
	previous_trains = trains.trains()
	logger = train_logger.Logger(ARGS = ARGS, database_config = database_config)
	# d_logger = debug_logger.DebugLogger(ARGS = ARGS)
	fps = 0
	total_moving_detects = 0
	while STREAM.isOpened():
		if DEBUG:
			fps = get_fps()
		if DFPS and not DEBUG:
			fps = get_fps()
			print('fps = ' + str(fps))
		_, image = STREAM.read()
		pil_image = Image.fromarray(image)
		# timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
		timestamp = datetime.now().timestamp()
		# detections = ENGINE.detect_with_image(Image.fromarray(image), threshold=CONF, top_k=10, keep_aspect_ratio=True, relative_coord=False)
		detections = ENGINE.detect_with_image(pil_image, threshold=CONF, top_k=10, keep_aspect_ratio=True, relative_coord=False)
		# first we try to log for offline debugging purposes. Thats why we keep threshold 0 then filter.
		train_detects = [d for d in detections if d.label_id == 6]
		# if d_logger.should_log():
		# 	d_logger.log(image, train_detects, timestamp)
		# train_detects = [d for d in detections if d.score >= CONF]
		# if len(train_detects) == 0:
		# 	print('no detects')
		# 	continue
		train_centroids = []
		current_trains = trains.trains()
		if len(train_detects) > 0:
			train_centroids = (np.array([d.bounding_box for d in train_detects])).sum(axis=1) / 2

		current_trains = trains.trains([d.bounding_box for d in train_detects],
						 train_centroids,
						 [int(d.score*100) for d in train_detects],
						 [0 for _ in train_detects]) # empy frames

		# Step 1 - Discounting previously recognized stationary trains from the current train detects .
		if stationary_trains.len() > 0:
			# Calculate distances between each pair of train detect centroids and stationary centroids.
			# Sort pairs by minimum distance and match unique paris with distances less
			# than DDS (Detect to Stationary Distance).
			used_rows, used_cols = [],[]
			if current_trains.len() > 0:
				(used_rows, used_cols) = match_min_dist(row_vector=np.array(stationary_trains.centroids),
														col_vector=current_trains.centroids, dist_limit=DDS)
			current_trains.filter_out(used_cols)
			stationary_trains.filter_stationary(used_rows, EFD)
		# Step 2 - Recognizing new stationary trains by comparing centroids from previous frames
		if previous_trains.len() > 0:
			# Calculate distances between each pair of (filtered) train detect centroids and stationary centroids.
			# Sort pairs by minimum distance and match unique paris with distances less
			# than DTS (Tracking to Stationary Distance).
			used_rows, used_cols = [],[]
			if current_trains.len() > 0:
				(used_rows, used_cols) = match_min_dist(row_vector=np.array(previous_trains.centroids),
													col_vector=np.array(current_trains.centroids), dist_limit=DTS)
			current_trains.filter_out(used_cols)
			previous_trains.filter_previous(used_rows, EFT, stationary_trains)
		previous_trains.extend(current_trains)
		logger.log(image = pil_image,
				moving_trains = current_trains,
		 		stationary_trains = stationary_trains,
		 		timestamp=timestamp)
		if DEBUG and not DFPS:
			debug_mul(current_trains, stationary_trains, image, fps)
			keyCode = cv2.waitKey(1) & 0xFF
			# Stop the program on the 'q' key
			if keyCode == ord("q"):
				break
		if DEBUG and DFPS:
			print('total_moving_detects = ' + str(total_moving_detects))



if __name__ == "__main__":
	# load config arguments
	ARGS = camera_config.ARGS
	# Load the DetectionEngine
	ENGINE = DetectionEngine(ARGS.model)
	if not ENGINE:
		print("Failed to load detection engine.")
		exit()
	# Read labels file
	LABELS = dataset_utils.read_label_file(ARGS.label)
	if not LABELS:
		print("Failed to load labels file")
		exit()
	# Setup image capture stream
	STREAM = cv2.VideoCapture(gstreamer_pipeline(capture_width = ARGS.width, capture_height = ARGS.height,
				display_width = ARGS.width, display_height = ARGS.height, framerate=ARGS.fps), cv2.CAP_GSTREAMER)

	try:
		if not STREAM.isOpened():
			STREAM.open()
		loop(STREAM, ENGINE, ARGS.debug, ARGS.confidence, ARGS.dts,
			 ARGS.dds, ARGS.eft, ARGS.efd, ARGS.debugonlyfps, ARGS)
		STREAM.release()
		cv2.destroyAllWindows()
	except KeyboardInterrupt:
		print("Program killed")
		STREAM.release()
		cv2.destroyAllWindows()








