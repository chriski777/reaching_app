from ximea import xiapi
import cam_Buffer.ImageTuple as imgTup
from cam_func.cameraSetup import cameraDev as cam_dev
from collections import deque
import cam_Buffer.serializeBuffer as serBuf
import cv2
import time
import datetime
import numpy as np

#Global Variables
font = cv2.FONT_HERSHEY_SIMPLEX
camera_list = []

def initialize_cam_list(num_cameras,cam_set_dict,init_time):
	global camera_list 
	camera_list = cam_dev(num_cameras,cam_set_dict,init_time).cameraList

def prepare_stream(num_cameras):
	img_dict = {}
	for i in range(num_cameras):
		img_dict[i] = xiapi.Image()
	#start data acquisition in parallel
	for i in range(num_cameras):
		camera_list[i].start_acquisition()
		print('Data acquisition for camera %d ready!' %(i))
	return img_dict

def stop_cam_acq(num_cameras, img_dict):
	for i in range(num_cameras):
		#stop data acquisition
		print('Stopping acquisition for camera %d ...' %i)
		camera_list[i].stop_acquisition()
		print("Total Frames for camera %d: %d" % (i,img_dict[i].nframe))
		#stop communication
		camera_list[i].close_device()

#Acquires the BaseCol of given area that we will use as threshold values.
def acquireBaseCol(curr_cam, avg_time,row1, row2, col):
	orig_setting = curr_cam.get_trigger_source()
	if (orig_setting !="XI_TRG_OFF"):
		#Necessary to stop acquisition as you can't change camera settings before stopping acquisition
		#Need to allow free_streaming mode to get frames 
		curr_cam.stop_acquisition()
		curr_cam.set_trigger_source("XI_TRG_OFF")
		curr_cam.start_acquisition()
	counter = 0
	sampNum = avg_time*int(curr_cam.get_framerate())
	baseMatrix = np.zeros(shape = (row2-row1, sampNum))
	img = xiapi.Image()
	try:
		print('Calculating BaselineCol...')
		while (counter < sampNum):
			curr_cam.get_image(img,timeout = 10000)
			data = img.get_image_data_numpy()
			baseMatrix[:,counter] = data[row1:row2,col]
			counter +=1
		print('Finished Calculating BaselineCol')
	except KeyboardInterrupt:
		cv2.destroyAllWindows()
	meanVector = np.mean(baseMatrix, axis = 1)
	k = np.zeros(shape = (sampNum,1))
	for i in range(0,sampNum):
		diffVec = baseMatrix[:,i] - meanVector
		k[i,:] = np.sum(np.square(diffVec))
	k_hat = np.mean(k)
	k_std = np.std(k)
	curr_cam.stop_acquisition()
	curr_cam.set_trigger_source(orig_setting)
	curr_cam.start_acquisition()
	#returning the nframe is necessary if we want to properly calculate the avg fps per second
	#the frameNumber is not reset after the acquisition of the base column vector. Reset of frame 
	#number only occurs with stopping acquistion.
	return (k_hat + 5*k_std, meanVector)

def calc_serial(serial_times):
	totalSerial = 0
	if serial_times:
		for ser_time in serial_times:
			totalSerial += ser_time
	return totalSerial

def label_images(cam_id,img,data_arr,intFrame):
	camera_id = 'Camera: ' + str(cam_id)
	frameNum = 'FrameNum : ' + str(img.nframe)
	ts = 'TimeStamp(s) : ' + str(img.tsSec)
	frameRate = 'FPS Setting: ' + str(camera_list[cam_id].get_framerate())
	currTime = "Current Time: " + str(datetime.datetime.now())
	avgFPS = 'Avg FPS(s) : {:5.1f}'.format(intFrame)
	cv2.putText(
		data_arr[cam_id], frameNum, (10,20), font, 0.5, (255, 255, 255), 1
	)
	cv2.putText(
		data_arr[cam_id], ts, (10,40), font, 0.5, (255, 255, 255), 1
		)
	cv2.putText(
		data_arr[cam_id], frameRate, (10,60), font, 0.5, (255, 255, 255), 1
		)
	cv2.putText(
		data_arr[cam_id], currTime, (10,80), font, 0.5, (255, 255, 255), 1
		)
	cv2.putText(
		data_arr[cam_id], avgFPS, (10,100), font, 0.5, (255, 255, 255), 1
		)
	cv2.putText(
		data_arr[cam_id], camera_id, (10,120), font, 0.5, (255, 255, 255), 1
	)

def cam_stream(img_dict,col_dict, stream_dict):
	num_cameras = len(camera_list)
	img_dict_arr = [img_dict[i] for i in range(num_cameras)]

	threshCounter = 0
	buffer_full = False
	image_buffer = deque()
	serial_times = deque()  #deque of all serial_times. Use deque because adding is constant time unlike list which is on order of n.

	init_time = stream_dict['init_time']
	queue_time = stream_dict['qt']
	show = stream_dict['show']
	path = stream_dict['path']

	threshold,meanBaseVector = acquireBaseCol(camera_list[0], col_dict['avg_time'], col_dict['row1'], col_dict['row2'], col_dict['col'])

	t0 = time.time()
	startTime = t0
	prev_frame = 0
	intFrame = camera_list[0].get_framerate()
	print('Starting data acquisition for all cameras')
	while True:
		try:
			#get data and pass them from camera to img, wait 10s for possible signals
			for i in range(num_cameras):
				camera_list[i].get_image(img_dict_arr[i], timeout = 5000)
			recentTime = time.time()
			#create numpy arr with data from camera. Dimensions of the arr are 
			#determined by imgdataformat
			data_arr = [img_dict_arr[i].get_image_data_numpy() for i in range(num_cameras)]
			#Recalculate Avg FPS every second (Only useful in free run mode not trigger mode)
			if (time.time() - startTime) > 1:
				intFrame = (img_dict_arr[0].nframe - prev_frame)
				prev_frame = img_dict_arr[0].nframe
				startTime = time.time()
			#show acquired image with frameNum, Timestamp, FPS Setting, current time, and avgFPS since 
			#the beginning of acquisition
			#Calculate camera's current frame rate
			for j in range(num_cameras):
				label_images(j,img_dict_arr[j],data_arr,intFrame)
				#Do only for first camera
				if j == 0:
					first_image = data_arr[j]
					diffVec = first_image[150:501, 300] - meanBaseVector
					k_real = np.sum(np.square(diffVec))
					if (k_real > threshold):
						threshCounter += 1
						#print(k_real,threshold)
					#imshow takes long so your buffer will not work properly if show != 0
					if (show == 1):
						cv2.imshow('XiCAM %s' % camera_list[0].get_device_name(), data_arr[0])
				#Remove first image in buffer if buffer is filled
				if (len(image_buffer) == num_cameras*queue_time*int(camera_list[j].get_framerate())):
					if not(buffer_full):
						buffer_full = True
						print("Buffer is full. Ready for Serialization!")
					removed = image_buffer.popleft()
				#Add tuple of image frame, date time, and numpy arr of image
				image_buffer.append(imgTup.ImageTuple(img_dict_arr[j].nframe, datetime.datetime.now(), data_arr[j]))
			cv2.waitKey(1)
		except KeyboardInterrupt:
			serial_time = serBuf.serialize(image_buffer,path)
			serial_times.append(serial_time)
			#Flush out the buffer
			#image_buffer = deque()
			buffer_full = False
			if (show == 1):
				cv2.destroyAllWindows()
		except xiapi.Xi_error as err:
			if err.status == 10:
				print("VDI not detected.")
			print (err)
			break
	stop_cam_acq(num_cameras,img_dict)
	totalSerial = calc_serial(serial_times)
	print("Total Serialization Time: %s " %str(totalSerial))
	print("Lag between start of program and start of acquisition: %s" % str(t0 - init_time))
	print("Total Acquisition Time: %s " % str(recentTime - t0))
	print("Total Time: %s " % str(recentTime - init_time))
	print('Done.')