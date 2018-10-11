from ximea import xiapi
from collections import deque
from cam_func.cameraSetup import cameraDev as cam_dev
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
exp_per = 4000 #Minimum trigger period is dependent on exposure time (microseconds)
gain_val = 5.0 #Gain: sensitivity of camera
imgdf = 'XI_RAW8' #Direct camera output with no processing. RAW8 is necessary to achieve full FPS capabilities!
sensor_feat = 1 #Set to 1 for faster FPS 
cam_set_dict = {'gpi_selector': "XI_GPI_PORT1", 'gpi_mode': "XI_GPI_OFF", 'trigger_source': "XI_TRG_OFF", 'gpo_selector': "XI_GPO_PORT1",
    'gpo_mode': "XI_GPO_OFF",'imgdf': imgdf, 'exp_per': exp_per, 'gain_val': gain_val, 'sensor_feat': sensor_feat}
queue_time = 5  #Image Buffer queue length (seconds)
num_cameras = 2 #Number of Cameras. Set this to 1 if you're only using one camera.

#Initialize cameras with user defined settings above
cam_devices = cam_dev(num_cameras,cam_set_dict,init_time)
camera_list = cam_devices.cameraList
#Initialize imageBuffers and Image objects for cameras. Also starts acquisitions for all cameras
img_buffer_dict, img_dict = prepare_stream(camera_list,num_cameras)

#CameraOne should be the camera that'll use thresholding based on column values.
cameraOne = camera_list[0]

base_frames,threshold,meanBaseVector = cam_devices.acquireBaseCol(cameraOne,5,150,501,300)
col_dict = {'num_bf': base_frames, 'th': threshold, 'mbv': meanBaseVector}
stream_dict = {'init_time':init_time,'qt': queue_time, 'show': 0, 'path': path}

cam_stream(camera_list, img_buffer_dict, img_dict,col_dict,stream_dict)