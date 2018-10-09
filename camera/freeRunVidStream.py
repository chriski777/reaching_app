from ximea import xiapi
from collections import deque
from cam_func.cameraSetup import cameraDev as cam_dev
from cam_func.camera_start_acq import prepare_stream
from cam_func.camera_start_acq import finish_stream

import cam_Buffer.ImageTuple as imgTup
import cv2
import time
import datetime
import numpy as np


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
#cameraTwo = camera_list[1]

img = img_dict[0]
imageBufferOne = img_buffer_dict[0]
# img2 = img_dict[1]
# imageBufferTwo = img_buffer_dict[1]
try:
    print('Starting video. Press CTRL+C to exit.')
    t0 = time.time()
    startTime = t0
    prev_frame = base_frames
    intFrame = cameraOne.get_framerate()
    threshCounter = 0
    while True:
        #get data and pass them from camera to img, wait 10s for possible signals
        cameraOne.get_image(img,timeout = 1000)
        #cameraTwo.get_image(img2,timeout = 1000)
        #create numpy array with data from camera. Dimensions of the array are 
        #determined by imgdataformat
        data = img.get_image_data_numpy()
        #datatwo = img2.get_image_data_numpy()
        #Recalculate Avg FPS every second (Only useful in free run mode not trigger mode)
        if (time.time() - startTime) > 1:
            intFrame = (img.nframe - prev_frame)
            prev_frame = img.nframe
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
        diffVec = data[150:501, 300] - meanBaseVector
        k_real = np.sum(np.square(diffVec))
        if (k_real > threshold):
            threshCounter += 1
            print(threshCounter)
        #Remove first image in buffer if buffer is filled
        if (len(imageBufferOne) == queue_time*int(cameraOne.get_framerate())):
            removed = imageBufferOne.popleft()
        #Add tuple of image frame, date time, and numpy array of image
        imageBufferOne.append(imgTup.ImageTuple(img.nframe,datetime.datetime.now(),data))
        #imageBufferTwo.append(imgTup.ImageTuple(img2.nframe,datetime.datetime.now(),datatwo))
        cv2.imshow('XiCAM %s' % cameraOne.get_device_name(), data)
        cv2.waitKey(1)
except KeyboardInterrupt:
    cv2.destroyAllWindows()

finish_stream(camera_list,num_cameras,base_frames,t0,init_time,img_buffer_dict,img_dict)
