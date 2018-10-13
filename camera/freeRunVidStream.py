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
exp_per = 4000 #Minimum trigger period is dependent on exposure time (microseconds)
gain_val = 5.0 #Gain: sensitivity of camera
imgdf = 'XI_RAW8' #Direct camera output with no processing. RAW8 is necessary to achieve full FPS capabilities!
sensor_feat = 1 #Set to 1 for faster FPS 
cam_set_dict = {'gpi_selector': "XI_GPI_PORT1", 'gpi_mode': "XI_GPI_OFF", 'trigger_source': "XI_TRG_OFF", 'gpo_selector': "XI_GPO_PORT1",
    'gpo_mode': "XI_GPO_OFF",'imgdf': imgdf, 'exp_per': exp_per, 'gain_val': gain_val, 'sensor_feat': sensor_feat}
queue_time = 2  #Image Buffer queue length (seconds)
num_cameras = 2 #Number of Cameras. Set this to 1 if you're only using one camera.

#Initialize cameras with user defined settings above
initialize_cam_list(num_cameras,cam_set_dict,init_time)
#Initialize imageBuffers and Image objects for cameras. Also starts acquisitions for all cameras
img_dict = prepare_stream(num_cameras)

col_dict = {'avg_time': 5, 'row1':150 , 'row2': 501, 'col': 300}
stream_dict = {'init_time':init_time,'qt': queue_time, 'show': 1, 'path': path}

cam_stream(img_dict,col_dict,stream_dict)