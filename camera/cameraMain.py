from ximea import xiapi
import cam_Buffer.ImageTuple as imgTup
import cam_Buffer.serializeBuffer as serBuf
import time
import datetime
import numpy as np
import serial
import binascii
import struct 
import os 

from collections import deque

dataDir = '/home/pns/Desktop/project'		#directory to save data

#camera settings 
numCams = 2
fps = 200
imgdataformat = "XI_RAW8" 					#raw camera output format (note: use XI_RAW8 for full fps) 
exposure = 10000 							#exposure time (microseconds) (note: determines minimum trigger period) 
gain = 20.0 									#gain: sensitivity of camera 
sensor_feature_value = 1
gpi_selector = "XI_GPI_PORT1" 
gpi_mode =  "XI_GPI_TRIGGER"#"XI_GPI_OFF"					
trigger_source = "XI_TRG_EDGE_RISING"#"XI_TRG_OFF"  
gpo_selector = "XI_GPO_PORT1"
gpo_mode = "XI_GPO_EXPOSURE_ACTIVE"#"XI_GPO_OFF"
fBufferDur = 1.5							#duration (sec) to buffer images for failed reaches
cBufferDur = fBufferDur + 2					#duration (sec) to buffer images for correct reaches (NOTE: should be consistent w/rewardWinDur defined in arduino)
show = 0								    #should images be displayed (0 for full fps)
camtimeout = 20000

#reach detection
baselineDur = 2								#duration to acquire images to compute baseline pixel statistics
startRow = 450
stopRow = 800
col = 550
stdThreshold = 10

#serial communication w/arduino
serial_path = '/dev/ttyACM0'
serial_baud = 115200
ardtimeout = 1000

#create a list of camera instances w/user-defined settings
camList = []
for i in range(numCams):
	print('opening camera %s ...' %(i))
	cam = xiapi.Camera(dev_id = i)
	cam.open_device()
	cam.set_imgdataformat(imgdataformat)
	cam.set_exposure(exposure)
	cam.set_gain(gain)
	if i==1:
		cam.set_gain(gain/2)
	cam.set_sensor_feature_value(sensor_feature_value)
	cam.set_gpi_selector(gpi_selector)
	cam.set_gpi_mode(gpi_mode)
	cam.set_trigger_source(trigger_source)
	cam.set_gpo_selector(gpo_selector)
	cam.set_gpo_mode(gpo_mode)
	camList.append(cam)

#create a dictionary of Image instances to store image data and metadata for each camera
#also start data acquisition for each camera
imgDict = {}
for i in range(numCams):
	imgDict[i] = xiapi.Image()
	camList[i].start_acquisition()
	print('data acquisition for camera %d ready' %(i))

#create serial communication object for arduino (must be done before baseline calculations to make sure lights are on)
ard_ser = serial.Serial(serial_path, serial_baud, timeout = ardtimeout)
time.sleep(2) #wait for arduino to wake up
ard_ser.flushInput()
ser_timeout = False
sendArd = 's' #character code for commands to arduino
#ask arduino for first line of data
ard_ser.write(sendArd)
newline = ard_ser.readline().split()
# 0 : count_trials = 0
# 1 : serPNS = '0'
# 2 : robotOutState = 1
# 3 : ecuPinState  = 0
# 4 : inRewardWin = 0
# 5 : rewardPinState = 1
# 6 : countRewards = 0
# 7 : lickVoltage = 0

#acquire baseline pixel statistics NOTE: currently only implemented for one camera
def acquireBaseline(curr_cam,avg_time,row1,row2, col,timeout):

	#initialize vars	
	counter = 0 #counts num images aquired
	sampNum = avg_time*int(curr_cam.get_framerate()) #total images to acquire
	baseMatrix = np.zeros(shape = (row2-row1, sampNum)) #stores acquired pixel values
	img = xiapi.Image() #image object used to acquire images

	#acquire pixel data from desired number of images
	while (counter < sampNum):
		curr_cam.get_image(img,timeout = timeout)
		baseMatrix[:,counter] = img.get_image_data_numpy()[row1:row2,col]
		counter +=1

	#compute pixel means and stds
	K_mean = np.mean(baseMatrix, axis = 1)
	k_std = np.std(np.sum(np.square(baseMatrix-K_mean.reshape(row2-row1,1)),axis=1))
	return (K_mean, k_std)

print('acquiring baseline')
meanBaseline,stdBaseline = acquireBaseline(camList[0],baselineDur,startRow,stopRow,col,camtimeout)

#open paths for writing data to
sensorpath = dataDir + "/sensor_data/"
camerapath = dataDir + "/camera/data/" + str(datetime.datetime.now())
if not os.path.isdir(sensorpath):
	os.makedirs(sensorpath)
if not os.path.isdir(camerapath):
	os.makedirs(camerapath)
sensorfile = sensorpath + str(datetime.datetime.now());    
outputfile = open(sensorfile, "w+");
header = "time countTrials serPNS robotOutState ecuPinState inRewardWin rewardPinState countRewards lickVoltage stdPixels"
outputfile.write(header + "\n");

#camera parameters/objects for main loop
imgdata = {}
buffer_full = False 
image_buffer = deque() #deque object that is buffer for both cameras. 
serial_times = deque()  #deque of all serial_times. deque is a high-performance list object w/fast appends/pops on either end

print('starting main loop')
print('trials completed:')
print(newline[0])
try:
	while True:

		#send arduino command so it can start printing data while image data is being captured
		ard_ser.write(sendArd)

		#get current time
		now = str(int(round(time.time()*1000))) 
		stdPixels = 0
		
		if newline[3]=='0': #ecu is triggering so get new image
			#pass data from camera to img
			camList[0].get_image(imgDict[0], timeout = camtimeout)
			camList[1].get_image(imgDict[1], timeout = camtimeout) 
			
			#convert img data to numpy (takes 1-2 ms)
			imgdata[0] = imgDict[0].get_image_data_numpy()
			imgdata[1] = imgDict[1].get_image_data_numpy()

			#compute pixelSD
			stdPixels = np.round(np.sum(np.square(imgdata[0][startRow:stopRow,col]-meanBaseline))/stdBaseline,decimals=1)
			imgdata[0][startRow:stopRow,col] = 0
			# print(stdPixels)

			# #display images
			# if (show == 1):
			# 	cv2.imshow('XiCAM %s' % camera_list[0].get_device_name(), data_arr[0])
			# 	cv2.waitKey(1) #necessary to make the video window the right size 

			#update buffer
			image_buffer.append(imgTup.ImageTuple(0, now, imgdata[0]))
			image_buffer.append(imgTup.ImageTuple(1, now, imgdata[1]))
			#buffer length is different for correct vs failed reaches
			if newline[4]=='1' and len(image_buffer)>numCams*cBufferDur*fps: #int(camList[0].get_framerate()) (replace fps for free run mode)
				#correct reach, remove old image in FIFO manner
				image_buffer.popleft()
				image_buffer.popleft()
			elif newline[4]=='0' and len(image_buffer)>numCams*fBufferDur*fps: #int(camList[0].get_framerate()) (replace fps for free run mode)
				#failed reach, remove old image in FIFO manner
				image_buffer.popleft()
				image_buffer.popleft()
		
		#send/receive data to/from arduino
		# oldmillis = int(round(time.time()*1000))
		newline = ard_ser.readline() #arduino sends a line of data back
		# newmillis = int(round(time.time()*1000))
		# print(newmillis-oldmillis)

		#write data to sensor file
		outputfile.write(now+" "+newline[0:-2:1]+" "+str(stdPixels)+"\n")

		#parse commands from arduino
		newline = newline.split() 
		if newline[1] == 's' and stdPixels>stdThreshold:
			#robot is in position, ecu is triggering, and a new reach has been detected			 
			sendArd = 'r' #tells arduino reach has been detected
		elif newline[1] == 'c': 
			#arduino said to save image buffer 
			serial_time = serBuf.serialize(image_buffer,camerapath,newline)
			print(newline[0] + ' success')
			sendArd = 's' #tells arduino image buffer has been saved
			image_buffer = deque() #flush out buffer
			# if (show == 1):
			# 	cv2.destroyAllWindows()
		elif newline[1] == 't': 
			#arduino said to save image buffer 
			serial_time = serBuf.serialize(image_buffer,camerapath,newline)
			print(newline[0] + ' fail')
			sendArd = 's' #tells arduino image buffer has been saved
			image_buffer = deque() #flush out buffer
			# if (show == 1):
			# 	cv2.destroyAllWindows()

	#close arduino connection
	ard_ser.close()
	#stop camera acquisition
	for i in range(numCams):
		#stop data acquisition
		print('Stopping acquisition for camera %d ...' %i)
		camList[i].stop_acquisition()
		print("Total Frames for camera %d: %d" % (i,imgDict[i].nframe))
		#stop communication
		camList[i].close_device()
	image_buffer = deque()
	if (show == 1):
		cv2.destroyAllWindows()
		
except KeyboardInterrupt:
	#close arduino connection
	ard_ser.close()
	#stop camera acquisition
	for i in range(numCams):
		#stop data acquisition
		print('Stopping acquisition for camera %d ...' %i)
		camList[i].stop_acquisition()
		print("Total Frames for camera %d: %d" % (i,imgDict[i].nframe))
		#stop communication
		camList[i].close_device()
	image_buffer = deque()
	if (show == 1):
		cv2.destroyAllWindows()
except xiapi.Xi_error as err:
	if err.status == 10:
		print("Triggers not detected.")
	print (err)
	