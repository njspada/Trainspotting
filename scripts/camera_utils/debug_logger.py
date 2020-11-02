from threading import Thread
from concurrent.futures import Future
import cv2
from datetime import datetime
from os import makedirs
import math

# threading related source from - 
# https://stackoverflow.com/questions/19846332/python-threading-inside-a-class
def call_with_future(fn, future, args, kwargs):
    try:
        result = fn(*args, **kwargs)
        future.set_result(result)
    except Exception as exc:
        future.set_exception(exc)

def threaded(fn):
    def wrapper(*args, **kwargs):
        future = Future()
        Thread(target=call_with_future, args=(fn, future, args, kwargs)).start()
        return future
    return wrapper

# Logs output for debug purposes
class DebugLogger:
    skipped_frames = 0
    skip_n = 60
    debug_output_path = "/from/ARGS"

    def __init__(self, ARGS):
        self.skip_n = ARGS.debug_skip_n
        self.debug_output_path         = ARGS.debug_output_path

    def should_log(self):
        if self.skipped_frames == skip_n-1:
            self.skipped_frames = 0
            return True
        self.skipped_frames += 1
        return False

    @threaded
    def log(self, IMAGE, TRAIN_DETECTS, TIMESTAMP):
        t = datetime.fromtimestamp(TIMESTAMP)
        date = t.strftime('%Y-%m-%d')
        makedirs(self.debug_output_path + date + '/images', exist_ok=True)
        logfilepath = self.debug_output_path + date + '/log.csv'
        imagefilepath = self.debug_output_path + '/' + date + '/images/' + str(TIMESTAMP) + '.jpg'
        if not cv2.imwrite(imagefilepath, IMAGE):
            print('----error saving debug image----')
            return
        with open(logfilepath, 'a') as logfile:
            if logfile.tell() == 0:
                # add headers
                header = "img_timestamp,i,score,x0,y0,x1,y1\n"
                logfile.write(header)
            for i,d in enumerate(TRAIN_DETECTS):
                # we have imagefilename, bounding boxes, score. all labels are trains (filetered in loop)
                line = [str(TIMESTAMP),str(i),str(int(d.score*100))]
                line.extend(d.bounding_box.flatten().astype(str).tolist())
                logfile.write(','.join(line) + '\n')










