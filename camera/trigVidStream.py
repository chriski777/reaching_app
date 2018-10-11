from ximea import xiapi
from collections import deque
from cam_func.cameraSetup import cameraDev as cam_dev
from cam_func.camera_start_acq import *
import cam_Buffer.ImageTuple as imgTup
import cam_Buffer.serializeBuffer as serBuf
import cv2
import time
import datetime
import h5py
import os 
import numpy as np

#Path that we save serialized files into 
path = '/media/pns/0e3152c3-1f53-4c52-b611-400556966cd8/trials/'
#Time since start of program
init_time = time.time()
#Values for BOTH cameras
exp_per = 4000 #Minimum trigger period is dependent on exposure time (microseconds)
gain_val = 5.0 #Gain: sensitivity of camera
imgdf = 'XI_RAW8' #Direct camera output with no processing. RAW8 is necessary to achieve full FPS capabilities!
sensor_feat = 1 #Set to 1 for faster FPS 
queue_time = 5  #Image Buffer queue length (seconds)
time_out = 5000 # time interval for trigger to occur before time_outError

buffer_full = False
cam_set_dict = {'gpi_selector': "XI_GPI_PORT1", 'gpi_mode': "XI_GPI_TRIGGER", 'trigger_source': "XI_TRG_EDGE_RISING", 'gpo_selector': "XI_GPO_PORT1",
	'gpo_mode': "XI_GPO_EXPOSURE_ACTIVE",'imgdf': imgdf, 'exp_per': exp_per, 'gain_val': gain_val, 'sensor_feat': sensor_feat}
num_cameras = 1

#Initialize cameras with user defined settings above
cam_devices = cam_dev(num_cameras,cam_set_dict,init_time)
camera_list = cam_devices.cameraList

cameraOne = camera_list[0]
#Initialize imageBuffers and Image objects for cameras. Also starts acquisitions for all cameras
img_buffer_dict, img_dict = prepare_stream(camera_list,num_cameras)

base_frames,threshold,meanBaseVector = cam_devices.acquireBaseCol(cameraOne,5,150,501,300)
col_dict = {'num_bf': base_frames, 'th': threshold, 'mbv': meanBaseVector}
stream_dict = {'qt': queue_time, 'show': 0, 'path': path}



while True:
	try:
		#get data and pass them from camera to img, wait 10s for possible signals
		cameraOne.get_image(img,time_out = time_out)
		#time of most recent image taken
		recentTime = time.time()
		#create numpy array with data from camera. Dimensions of the array are 
		#determined by imgdataformat
		data = img.get_image_data_numpy()
		
		#Recalculate Avg FPS every second (Only useful in free run mode not trigger mode)
		if (time.time() - startTime) > 1:
			intFrame = (img.nframe - prevFrame)
			prevFrame = img.nframe
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
		#Remove first image in buffer if buffer is filled
		if (len(imageBuffer) == queue_time*int(cameraOne.get_framerate())):
			if not(buffer_full):
				buffer_full = True
				print("Buffer is full. Ready for Serialization!")
			removed = imageBuffer.popleft()
			#print('Frame %d Image popped' % removed.frameNum)
		#Add tuple of image frame, date time, and numpy array of image
		imageBuffer.append(imgTup.ImageTuple(img.nframe,datetime.datetime.now(),data))
		#cv2.imshow('XiCAM %s' % cameraOne.get_device_name(), data)
		cv2.waitKey(1)
	except KeyboardInterrupt:
		serialTime = serBuf.serialize(imageBuffer,path)
		serial_times.append(serialTime)
		#Flush out the buffer
		imageBuffer = deque()
		buffer_full = False
	except xiapi.Xi_error as err:
		if err.status == 10:
			print("VDI not detected.")
		print (err)
		#stop data acquisition
		print('Stopping acquisition...')
		cameraOne.stop_acquisition()
		lagTime = t0 - init_time
		print("Lag between start of program and start of acquisition: %s" % str(lagTime))
		try:
			recentTime
		except NameError:
			print("No acquisition occured.")
		else:
			totalSerial = 0
			if serial_times:
				for i in serial_times:
					totalSerial += i
			print ("Available Bandwidth for camera 1: %s " % cameraOne.get_available_bandwidth())
			# print ("Available Bandwidth for camera 2: %s " % cameraTwo.get_available_bandwidth())
			print("Total Serialization Time: %s " %str(totalSerial))
			print("Total Acquisition Time: %s " % str(recentTime - t0)) #Includes time of serialization
			print("Total Frames: %d" % (img.nframe + 1))
		#stop communication
		cameraOne.close_device()
		#timeArray = np.array(trigTimes)
		#np.savetxt('camTimes.csv', timeArray, delimiter = ",", fmt = '%s')
		print('Done.')
		break
