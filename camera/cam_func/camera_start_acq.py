from ximea import xiapi
import cam_Buffer.ImageTuple as imgTup
from cam_func.cameraSetup import cameraDev as cam_dev
from collections import deque
import cam_Buffer.serializeBuffer as serBuf
import cv2
import time
import datetime
import numpy as np

def prepare_stream(camera_list,num_cameras):
	img_buf_dict = {}
	img_dict = {}
	for i in range(num_cameras):
		img_buf_dict[i] = deque()
		img_dict[i] = xiapi.Image()
	#start data acquisition in parallel
	for i in range(num_cameras):
		camera_list[i].start_acquisition()
		print('Starting data acquisition for camera %d' %(i))
	return img_buf_dict, img_dict

def cam_stream(camera_list,img_buf_dict, img_dict,col_dict, stream_dict):
	num_cameras = len(camera_list)
	img_dict_arr = [img_dict[i] for i in range(num_cameras)]
	img_buf_arr = [img_buf_dict[i] for i in range(num_cameras)]
	serial_times_arr = [deque() for i in range(num_cameras)]  #deque of all serial_times. Use deque because adding is constant time unlike list which is on order of n.

	base_frames = col_dict['num_bf']
	threshold = col_dict['th'] 
	meanBaseVector = col_dict['mbv']

	init_time = stream_dict['init_time']
	queue_time = stream_dict['qt']
	show = stream_dict['show']
	path = stream_dict['path']

	t0 = time.time()
	startTime = t0
	prev_frame = base_frames
	intFrame = camera_list[0].get_framerate()
	threshCounter = 0
	buffer_full = False

	while True:
		try:
			#get data and pass them from camera to img, wait 10s for possible signals
			for i in range(num_cameras):
				camera_list[i].get_image(img_dict_arr[i], timeout = 1000)
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
			font = cv2.FONT_HERSHEY_SIMPLEX
			#Calculate camera's current frame rate
			for j in range(num_cameras):
				frameNum = 'FrameNum : ' + str(img_dict_arr[j].nframe - base_frames)
				ts = 'TimeStamp(s) : ' + str(img_dict_arr[j].tsSec)
				frameRate = 'FPS Setting: ' + str(camera_list[j].get_framerate())
				currTime = "Current Time: " + str(datetime.datetime.now())
				avgFPS = 'Avg FPS(s) : {:5.1f}'.format(intFrame)
				cv2.putText(
					data_arr[j], frameNum, (10,20), font, 0.5, (255, 255, 255), 1
				)
				cv2.putText(
					data_arr[j], ts, (10,40), font, 0.5, (255, 255, 255), 1
					)
				cv2.putText(
					data_arr[j], frameRate, (10,60), font, 0.5, (255, 255, 255), 1
					)
				cv2.putText(
					data_arr[j], currTime, (10,80), font, 0.5, (255, 255, 255), 1
					)
				cv2.putText(
					data_arr[j], avgFPS, (10,100), font, 0.5, (255, 255, 255), 1
					)
				#Do only for first camera
				if j == 0:
					first_image = data_arr[j]
					diffVec = first_image[150:501, 300] - meanBaseVector
					k_real = np.sum(np.square(diffVec))
					if (k_real > threshold):
						threshCounter += 1
						#print(threshCounter)
					#imshow takes long so your buffer will not work properly if the code below is uncommented
					if (show == 1):
						cv2.imshow('XiCAM %s' % camera_list[0].get_device_name(), data_arr[0])
				#Remove first image in buffer if buffer is filled
				curr_buffer = img_buf_dict[j]
				if (len(curr_buffer) == queue_time*int(camera_list[j].get_framerate())):
					if not(buffer_full):
						buffer_full = True
						print("Buffer is full. Ready for Serialization!")
					removed = curr_buffer.popleft()
				#Add tuple of image frame, date time, and numpy arr of image
				curr_buffer.append(imgTup.ImageTuple(img_dict_arr[j].nframe, datetime.datetime.now(), data_arr[j]))
			cv2.waitKey(1)
		except KeyboardInterrupt:
			for k in range(num_cameras):
				image_buf =  img_buf_dict[k]
				serial_time = serBuf.serialize(image_buf,path)
				serial_times_arr[k].append(serial_time)
				#Flush out the buffer
				img_buf_dict[k] = deque()
			buffer_full = False
			if (show == 1):
				cv2.destroyAllWindows()
		except xiapi.Xi_error as err:
			if err.status == 10:
				print("VDI not detected.")
			print (err)
			break
	for i in range(num_cameras):
		#stop data acquisition
		print('Stopping acquisition for camera %d ...' %i)
		camera_list[i].stop_acquisition()
		totalSerial = 0
		if serial_times_arr[i]:
			for ser_time in serial_times_arr[i]:
					totalSerial += ser_time
		print("Total Serialization Time for camera %d: %s " %(i,str(totalSerial)))
		print("Total Frames for camera %d: %d" % (i,img_dict[i].nframe-base_frames))
		print("Image Buffer for camera %d Length: %d" % (i,len(img_buf_dict[i])))
		print("Image Buffer for camera %d contains frames from: %d to %d" %(i,img_buf_dict[i][0].frameNum,img_buf_dict[i][len(img_buf_dict[i]) -1].frameNum))
		#stop communication
		camera_list[i].close_device()
	print("Lag between start of program and start of acquisition: %s" % str(t0 - init_time))
	print("Total Acquisition Time: %s " % str(recentTime - t0))
	print("Total Time: %s " % str(recentTime - init_time))
	print('Done.')