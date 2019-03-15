from ximea import xiapi
from collections import deque
import PIL.Image, PIL.ImageTk
import Tkinter as tki 
import threading 
import cv2
import time
import cam_func.camera_start_acq as csa
class CameraApp(tki.Frame):
	def __init__(self, window, window_title):
		self.window = window
		self.window.title(window_title)
		self.vid_stream = VideoStream()
		self.canvas = tki.Canvas(window, width = self.vid_stream.img_width, height = self.vid_stream.img_height)
		self.canvas.pack()
		self.delay = 15
		self.update()
		self.window.mainloop()
		
	def update(self):
		ret = csa.grab_image(self.vid_stream.num_cameras, self.vid_stream.img_dict)
		if ret:
			data_arr = [self.vid_stream.img_dict[i].get_image_data_numpy() for i in range(self.vid_stream.num_cameras)]
			self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(data_arr[0]))
			self.canvas.create_image(0,0, image = self.photo, anchor = tki.NW)
		self.window.after(self.delay,self.update)

	def createWidgets(self):
		self.free_run_btn = tki.Button(self)
		self.free_run_btn["text"] = "Free Run "
		self.free_run_btn["command"] =  self.free_run 

		self.free_run_btn.pack({"side": "left"})

		self.draw_polygon = tki.Button(self)
		self.draw_polygon["text"] = "Hello"
		self.draw_polygon["command"] = self.free_run

		self.draw_polygon.pack({"side": "left"})
class VideoStream:
	def __init__(self):
		self.acquisition = False
		self.initialize_cameras()
		self.img_width = csa.get_img_width()
		self.img_height = csa.get_img_height()

	def initialize_cameras(self):
		init_time = time.time()
		#Values for BOTH cameras
		exp_per = 16000 #Minimum trigger period is dependent on exposure time (microseconds)
		gain_val = 20.0 #Gain: sensitivity of camera
		imgdf = 'XI_RAW8' #Direct camera output with no processing. RAW8 is necessary to achieve full FPS capabilities!
		sensor_feat = 1 #Set to 1 for faster FPS 
		cam_set_dict = {'gpi_selector': "XI_GPI_PORT1", 
						'gpi_mode': "XI_GPI_OFF", 
						'trigger_source': "XI_TRG_OFF", 
						'gpo_selector': "XI_GPO_PORT1",
						'gpo_mode': "XI_GPO_OFF",
						'imgdf': imgdf, 
						'exp_per': exp_per, 
						'gain_val': gain_val, 
						'sensor_feat': sensor_feat}
		queue_time = 50  #Image Buffer queue length (seconds)
		self.num_cameras = 1 #Number of Cameras. Set this to 1 if you're only using one camera.
		#Initialize cameras with user defined settings above
		csa.initialize_cam_list(self.num_cameras,cam_set_dict,init_time)
		self.img_dict = csa.prepare_stream(self.num_cameras)
		self.acquisition = True

	def __del__(self):
		if self.acquisition:
			csa.stop_cam_acq(self.num_cameras, self.img_dict)
		return

CameraApp(tki.Tk(), "Camera GUI")