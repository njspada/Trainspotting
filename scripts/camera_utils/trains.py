import copy

class trains: # object to hold info about detected trains
	bounding_boxes = []
	centroids = []
	empty_frames = []
	scores = []

	def __init__(self, l_bounding_box = [], l_centroid = [], l_scores = [], l_empty_frames = []):
		self.bounding_boxes = l_bounding_box
		self.centroids = l_centroid
		self.empty_frames = l_empty_frames
		self.scores = l_scores

	def add(self, bounding_box, centroid, score, frames = 0):
		self.bounding_boxes.append(bounding_box)
		self.centroids.append(centroid)
		self.empty_frames.append(frames)
		self.scores.append(score)

	def remove_at(self, index):
		if index < len(self.centroids):
			del self.bounding_boxes[index]
			del self.centroids[index]
			del self.empty_frames[index]
			del self.scores[index]

	def len(self):
		return len(self.centroids)

	def copy(self, target):
		self.bounding_boxes = copy.deepcopy(target.bounding_boxes)
		self.centroids = copy.deepcopy(target.centroids)
		self.empty_frames = copy.deepcopy(target.empty_frames)
		self.scores = copy.deepcopy(target.scores)

	def extend(self, target, refresh = False):
		if refresh:
			self.bounding_boxes = []
			self.centroids = []
			self.empty_frames = []
			self.scores = []
		self.bounding_boxes.extend(target.bounding_boxes)
		self.centroids.extend(target.centroids)
		self.empty_frames.extend(target.empty_frames)
		self.scores.extend(target.scores)

	def filter_out(self, indices):
		self.bounding_boxes = [b for i,b in enumerate(self.bounding_boxes) if i not in indices]
		self.centroids = [c for i,c in enumerate(self.centroids) if i not in indices]
		self.empty_frames = [f for i,f in enumerate(self.empty_frames) if i not in indices]
		self.scores = [s for i,s in enumerate(self.scores) if i not in indices]

	def filter_stationary(self, used_indices, EFD): # returns new object with filtered data
		# used rows/indices = stationary centroids that were matched with train detects in current frames.
		# We need to retain those.
		# Also retain centroids that have not been detected for up
		# to EFD frames (Empty Frames for Detection).
		temp = trains(l_bounding_box = [], l_centroid = [], l_scores = [], l_empty_frames = [])
		for i in range(self.len()):
			if i in used_indices:
				temp.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], 0)
			elif self.empty_frames[i] < EFD:
				temp.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], self.empty_frames[i]+1)
		self.copy(temp)

	def filter_previous(self, used_indices, EFT, stat_trains):
		# used indecices = previous centroids that are matched with current detects.
		# these previous centroids need to be marked as stationary trains.
		# previous centroids not matched with a train detect for more \
		# than EFT (Empty Frames for Tracking) consecutive frames will be discarded.
		temp_previous = trains(l_bounding_box = [], l_centroid = [], l_scores = [], l_empty_frames = [])
		for i in range(self.len()):
			if i in used_indices:
				stat_trains.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], 0)
			elif self.empty_frames[i] < EFT:
				temp_previous.add(self.bounding_boxes[i], self.centroids[i], self.scores[i], self.empty_frames[i]+1)
		self.extend(temp_previous, refresh = True)
		# self.copy(temp_previous)

	def print_lens(self):
		print('-----lenghts------')
		print('bounding_boxes = ' + str(len(self.bounding_boxes)))
		print('centroids = ' + str(len(self.centroids)))
		print('empty_frames = ' + str(len(self.empty_frames)))
		print('scores = ' + str(len(self.scores)))