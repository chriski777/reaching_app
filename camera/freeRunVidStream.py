from ximea import xiapi
from collections import deque
from cam_func.camera_start_acq import *

import cam_Buffer.ImageTuple as imgTup
import cv2
import time
import datetime
import numpy as np

#Path that we save serialized files into 
path = '/media/pns/0e3152c3-1f53-4c52-b611-400556966cd8/trials/'
#Time since start of program
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
num_cameras = 1 #Number of Cameras. Set this to 1 if you're only using one camera.

#Initialize cameras with user defined settings above
initialize_cam_list(num_cameras,cam_set_dict,init_time)
#Initialize imageBuffers and Image objects for cameras. Also starts acquisitions for all cameras
img_dict = prepare_stream(num_cameras)

col_dict = {'avg_time': 1, #time (sec) we'll record baseline images for
			'row1':150 ,  #row start index for desired pixels
			'row2': 501,  #row stop index 
			'col': 300,	  #column index
			'num_std': 3} #number of standard deviations for threshold calculation 

stream_dict = {'init_time': init_time, 
			   'qt': queue_time, #image buffer duration (seconds)
			   'show': 1, #display images or not (note: setting to 1 does not achieve full fps)
			   'path': '/home/pns/Desktop/project', #path that we save data files into 
			   'serial_path': '/dev/ttyACM0', #device name of Arduino
			   'serial_baud': 115200, #must be same on Arduino
			   'timeout': 2000, 
			   'label_images': False} #time (millisec) w/no new data before program terminates


cam_stream(img_dict,col_dict,stream_dict)