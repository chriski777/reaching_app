import numpy as np
import datetime as dt
class ImageTuple():
    def __init__(self,frameNum, dateTime, img):
    	if not isinstance(frameNum, long):
    		raise TypeError("Frame Number must be a number")
    	if not isinstance(dateTime, dt.datetime):
    		raise TypeError("DateTime must be a datetime.datetime object")
    	if not isinstance(img, np.ndarray):
    		raise TypeError("Image must be a Numpy array")
        self.title = str("Frame: %d, DateTime: %s" %(frameNum, dateTime))
        self.img = img

