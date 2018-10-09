from ximea import xiapi
import numpy as np

class cameraDev():
	#Initialize all camera devices to user defined camera settings
	def __init__(self,num_cams,camSetDict,init_time):
		self.cameraList = []
		self.init_time = init_time
		for i in range(num_cams):
			camera = xiapi.Camera(dev_id = i)
			#start communication
			print('Opening camera %s ...' %(i))
			camera.open_device()
			camera.set_imgdataformat(camSetDict['imgdf'])
			camera.set_exposure(camSetDict['exp_per'])
			camera.set_gain(camSetDict['gain_val'])
			camera.set_sensor_feature_value(camSetDict['sensor_feat'])
			camera.set_gpi_selector(camSetDict['gpi_selector'])
			camera.set_gpi_mode(camSetDict['gpi_mode'])
			camera.set_trigger_source(camSetDict['trigger_source'])
			camera.set_gpo_selector(camSetDict['gpo_selector'])
			camera.set_gpo_mode(camSetDict['gpo_mode'])
			self.cameraList.append(camera)
		self.printCamSet()
	#Prints the settings of each camera
	def printCamSet(self):
		counter = 0
		for i in range(len(self.cameraList)):
			currCamera = self.cameraList[i]
			print ('Camera %d Settings: ' %i)
			print('Exposure was set to %i us' %currCamera.get_exposure())
			print('Gain was set to %f db' %currCamera.get_gain())
			print('Img Data Format set to %s' %currCamera.get_imgdataformat())
			print ("Available Bandwidth for camera %d: %s " % (i,currCamera.get_available_bandwidth()))
			counter +=1 
	#Acquires the BaseCol of given area that we will use as threshold values.
	def acquireBaseCol(self,curr_cam,avgTime,row1, row2, col):
		counter = 0
		img = xiapi.Image()
		sampNum = avgTime*int(curr_cam.get_framerate())
		baseMatrix = np.zeros(shape = (row2-row1, sampNum))
		try:
			print('Calculating BaselineCol...')
			while (counter < sampNum):
				curr_cam.get_image(img,timeout = 10000)
				data = img.get_image_data_numpy()
				baseMatrix[:,counter] = data[row1:row2,col]
				counter +=1
		except KeyboardInterrupt:
			cv2.destroyAllWindows()
		meanVector = np.mean(baseMatrix, axis = 1)
		print(meanVector)
		k = np.zeros(shape = (sampNum,1))
		for i in range(0,sampNum):
			diffVec = baseMatrix[:,i] - meanVector
			k[i,:] = np.sum(np.square(diffVec))
		k_hat = np.mean(k)
		k_std = np.std(k)
		#returning the nframe is necessary if we want to properly calculate the avg fps per second
		#the frameNumber is not reset after the acquisition of the base column vector. Reset of frame 
		#number only occurs with stopping acquistion.
		return (img.nframe,k_hat + 5*k_std, meanVector)