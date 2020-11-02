def pipeline(
	ARGS
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
			ARGS.width,
			ARGS.height,
			ARGS.fps,
			0,
			ARGS.width,
			ARGS.height,
		)
	)