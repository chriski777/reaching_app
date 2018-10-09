from ximea import xiapi
import cam_Buffer.ImageTuple as imgTup
from cam_func.cameraSetup import cameraDev as cam_dev
from collections import deque
import cv2
import time
import datetime
import numpy as np

def prepare_stream(camera_list,num_cameras):
	imgBuffer_dict = {}
	img_dict = {}
	for i in range(num_cameras):
		imgBuffer_dict[i] = deque()
		img_dict[i] = xiapi.Image()
	#start data acquisition in parallel
	for i in range(num_cameras):
		camera_list[i].start_acquisition()
		print('Starting data acquisition for camera %d' %(i))
	return imgBuffer_dict, img_dict

def begin_stream(camera_list,):
	try:
	    print('Starting video. Press CTRL+C to exit.')
	    t0 = time.time()
	    startTime = t0
	    intFrame = cameraOne.get_framerate()
	    threshCounter = 0
	    while True:
	        #get data and pass them from camera to img, wait 10s for possible signals
	        cameraOne.get_image(img,timeout = 10000)
	        #create numpy array with data from camera. Dimensions of the array are 
	        #determined by imgdataformat
	        data = img.get_image_data_numpy()
	        
	        #Recalculate Avg FPS every second (Only useful in free run mode not trigger mode)
	        if (time.time() - startTime) > 1:
	            intFrame = (img.nframe - prev_frame)
	            prev_frame = img.nframe
	            startTime = time.time()
	        #show acquired image with frameNum, Timestamp, FPS Setting, current time, and avgFPS since 
	        #the beginning of acquisition
	        font = cv2.FONT_HERSHEY_SIMPLEX
	        #Calculate camera's current frame rate
	        frameNum = 'FrameNum : ' + str(img.nframe)
	        ts = 'TimeStamp(s) : ' + str(img.tsSec)
	        frameRate = 'FPS Setting: ' + str(cameraOne.get_framerate())
	        currTime = "Current Time: " + str(datetime.datetime.now())
	        avgFPS = 'Avg FPS(s) : {:5.1f}'.format(intFrame)
	        cv2.putText(
	            data, frameNum, (10,20), font, 0.5, (255, 255, 255), 1
	            )
	        cv2.putText(
	            data, ts, (10,40), font, 0.5, (255, 255, 255), 1
	            )
	        cv2.putText(
	            data, frameRate, (10,60), font, 0.5, (255, 255, 255), 1
	            )
	        cv2.putText(
	            data, currTime, (10,80), font, 0.5, (255, 255, 255), 1
	            )
	        cv2.putText(
	            data, avgFPS, (10,100), font, 0.5, (255, 255, 255), 1
	            )
	        diffVec = data[150:501, 300] - meanBaseVector
	        k_real = np.sum(np.square(diffVec))
	        if (k_real > threshold):
	            threshCounter += 1
	            print(threshCounter)
	        #Remove first image in buffer if buffer is filled
	        if (len(imageBufferOne) == queue_time*int(cameraOne.get_framerate())):
	            removed = imageBufferOne.popleft()
	        #Add tuple of image frame, date time, and numpy array of image
	        imageBufferOne.append(imgTup.ImageTuple(img.nframe,datetime.datetime.now(),data))
	        cv2.imshow('XiCAM %s' % cameraOne.get_device_name(), data)
	        cv2.waitKey(1)
	except KeyboardInterrupt:
	    cv2.destroyAllWindows()
def finish_stream(camera_list,num_cameras,base_frames,t0,init_time,img_buf_dict,img_dict):
	for i in range(num_cameras):
		#stop data acquisition
		print('Stopping acquisition for camera %d ...' %i)
		camera_list[i].stop_acquisition()
		print("Total Frames for camera %d: %d" % (i,img_dict[i].nframe-base_frames))
		print("Image Buffer for camera %d Length: %d" % (i,len(img_buf_dict[i])))
		print("Image Buffer for camera %d contains frames from: %d to %d" %(i,img_buf_dict[i][0].frameNum,img_buf_dict[i][len(img_buf_dict[i]) -1].frameNum))
		#stop communication
		camera_list[i].close_device()
	print("Lag between start of program and start of acquisition: %s" % str(t0 - init_time))
	print("Total Acquisition Time: %s " % str(time.time() - t0))
	print('Done.')