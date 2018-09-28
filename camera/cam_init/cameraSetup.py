from ximea import xiapi

class cameraDev():
	def __init__(self,devId,imgdf, exp_per, gain_val, sensor_feat,camSetDict):
		self.camera = xiapi.Camera(dev_id = devId)
		#start communication
		print('Opening camera %s ...' %(devId))
		self.camera.open_device()
		self.camera.set_imgdataformat(imgdf)
		self.camera.set_exposure(exp_per)
		self.camera.set_gain(gain_val)
		self.camera.set_sensor_feature_value(sensor_feat)
		self.camera.set_gpi_selector(camSetDict['gpi_selector'])
		self.camera.set_gpi_mode(camSetDict['gpi_mode'])
		self.camera.set_trigger_source(camSetDict['trigger_source'])
		self.camera.set_gpo_selector(camSetDict['gpo_selector'])
		self.camera.set_gpo_mode(camSetDict['gpo_mode'])