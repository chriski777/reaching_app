from ximea import xiapi
from collections import deque
import ImageTuple as imgTup
import cv2
import time
import datetime
import h5py
import os 
import numpy as np

#Time since start of program
init_time = time.time()
#Values for BOTH cameras
exp_per = 4000 #Minimum trigger period is dependent on exposure time (microseconds)
gain_val = 5.0 #Gain: sensitivity of camera
imgdf = 'XI_RAW8' #Direct camera output with no processing. RAW8 is necessary to achieve full FPS capabilities!
sensor_feat = 1 #Set to 1 for faster FPS 
queueTime = 5  #Image Buffer queue length (seconds)
timeOut = 5000 # time interval for trigger to occur before TimeOutError
serialTimes = deque() #deque of all serialTimes. Use deque because adding is constant time unlike list which is on order of n.
trigTimes = deque() #deque of timestamps for each trigger input 

cameraOne = xiapi.Camera(dev_id = 0)
#cameraTwo = xiapi.Camera(dev_id = 1)
#Path that we save serialized files into 
path = '/media/pns/0e3152c3-1f53-4c52-b611-400556966cd8/trials/'

#Function for serializing the imageBuffer
def serialize(imageBuffer):
	#SERIALIZE WITH HDF5
	#Create Unique Trial names
	#Turn VDO on to alert ECU to wait until serialization over
	#cameraOne.set_gpo_mode("XI_GPO_ON")
	trial_fn = 'myfile3.hdf5'
	if not os.path.isdir(path):
		os.makedirs(path)
	hdfStart = time.time()
	h = h5py.File(os.path.join(path, trial_fn), 'w', libver='latest')
	for i in imageBuffer:
		h.create_dataset(i.title, data=i.img)
	hdfEnd = time.time()
	serialTime = hdfEnd - hdfStart
	print("Time it took to serialize hdf5: %f ms" % ((serialTime)*1000))
	print("Image Buffer Length: %d" % len(imageBuffer))
	print("Image Buffer contains frames from: %d to %d" %(imageBuffer[0].frameNum,imageBuffer[len(imageBuffer) -1].frameNum))
	serialTimes.append(serialTime)
	#turn GPO off 
	#cameraOne.set_gpo_mode("XI_GPO_OFF")

#start communication
print('Opening first camera...')
cameraOne.open_device()
# print('Opening second camera...')
# cameraTwo.open_device()


#Initialize settings for both cameras
cameraOne.set_imgdataformat(imgdf)
cameraOne.set_exposure(exp_per)
cameraOne.set_gain(gain_val)
cameraOne.set_sensor_feature_value(sensor_feat)

# cameraTwo.set_imgdataformat(imgdf)
# cameraTwo.set_exposure(exp_per)
# cameraTwo.set_gain(gain_val)
# cameraTwo.set_sensor_feature_value(sensor_feat)

#Prepare camera for trigger mode on rising edge of input signal
cameraOne.set_gpi_selector("XI_GPI_PORT1")
cameraOne.set_gpi_mode("XI_GPI_TRIGGER")
cameraOne.set_trigger_source("XI_TRG_EDGE_RISING")

# cameraTwo.set_gpi_selector("XI_GPI_PORT1")
# cameraTwo.set_gpi_mode("XI_GPI_TRIGGER")
# cameraTwo.set_trigger_source("XI_TRG_EDGE_RISING")

cameraOne.set_gpo_selector("XI_GPO_PORT1")
cameraOne.set_gpo_mode("XI_GPO_EXPOSURE_ACTIVE")

print ('Camera One Settings: ')
print('Exposure was set to %i us' %cameraOne.get_exposure())
print('Gain was set to %f db' %cameraOne.get_gain())
print('Img Data Format set to %s' %cameraOne.get_imgdataformat())

# print ('Camera Two Settings: ')
# print('Exposure was set to %i us' %cameraTwo.get_exposure())
# print('Gain was set to %f db' %cameraTwo.get_gain())
# print('Img Data Format set to %s' %cameraTwo.get_imgdataformat())

#create imageBuffers with dequeue
imageBuffer = deque()
#imageBufferTwo = deque()

#create instance of Image to store image data and metadata
img = xiapi.Image()
#imgTwo = xiapi.Image()

#start data acquisition
print('Starting data acquisition...')
cameraOne.start_acquisition()
#cameraTwo.start_acquisition()

print('Starting video. Press CTRL+C to record. ')
t0 = time.time()
startTime = t0
prevFrame = 0
intFrame = cameraOne.get_framerate()

while True:
	try:
		#get data and pass them from camera to img, wait 10s for possible signals
		cameraOne.get_image(img,timeout = timeOut)
		#time of most recent image taken
		recentTime = time.time()
		trigTimes.append(recentTime)
		#print('Image %d Acquired' % img.nframe)
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
		if (len(imageBuffer) == queueTime*int(cameraOne.get_framerate())):
			removed = imageBuffer.popleft()
			#print('Frame %d Image popped' % removed.frameNum)
		#Add tuple of image frame, date time, and numpy array of image
		imageBuffer.append(imgTup.ImageTuple(img.nframe,datetime.datetime.now(),data))
		#cv2.imshow('XiCAM %s' % cameraOne.get_device_name(), data)
		cv2.waitKey(1)
	except KeyboardInterrupt:
		cv2.destroyAllWindows()
		serialize(imageBuffer)
		#Flush out the buffer
		imageBuffer = deque()
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
			if serialTimes:
				for i in serialTimes:
					totalSerial += i
			print ("Available Bandwidth for camera 1: %s " % cameraOne.get_available_bandwidth())
			# print ("Available Bandwidth for camera 2: %s " % cameraTwo.get_available_bandwidth())
			print("Total Serialization Time: %s " %str(totalSerial))
			print("Total Acquisition Time: %s " % str(recentTime - t0)) #Includes time of serialization
			print("Total Frames: %d" % (img.nframe + 1))
		#stop communication
		cameraOne.close_device()

		timeArray = np.array(trigTimes)
		np.savetxt('camTimes.csv', timeArray, delimiter = ",", fmt = '%s')
		print('Done.')
		break
