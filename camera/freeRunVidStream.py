from ximea import xiapi
from collections import deque
import ImageTuple as imgTup
import cv2
import time
import datetime

#Time since start of program
init_time = time.time()
#Values for BOTH cameras
exp_per = 4000 #Minimum trigger period is dependent on exposure time (microseconds)
gain_val = 5.0 #Gain: sensitivity of camera
imgdf = 'XI_RAW8' #Direct camera output with no processing. RAW8 is necessary to achieve full FPS capabilities!
sensor_feat = 1 #Set to 1 for faster FPS 

queueTime = 5  #Image Buffer queue length (seconds)

cameraOne = xiapi.Camera(dev_id = 0)
cameraTwo = xiapi.Camera(dev_id = 1)
#start communication
print('Opening first camera...')
cameraOne.open_device()
print('Opening second camera...')
cameraTwo.open_device()
#Initialize settings for both cameras
cameraOne.set_imgdataformat(imgdf)
cameraOne.set_exposure(exp_per)
cameraOne.set_gain(gain_val)
cameraOne.set_sensor_feature_value(sensor_feat)

cameraTwo.set_imgdataformat(imgdf)
cameraTwo.set_exposure(exp_per)
cameraTwo.set_gain(gain_val)
cameraTwo.set_sensor_feature_value(sensor_feat)

print ('Camera One Settings: ')
print('Exposure was set to %i us' %cameraOne.get_exposure())
print('Gain was set to %f db' %cameraOne.get_gain())
print('Img Data Format set to %s' %cameraOne.get_imgdataformat())

print ('Camera Two Settings: ')
print('Exposure was set to %i us' %cameraTwo.get_exposure())
print('Gain was set to %f db' %cameraTwo.get_gain())
print('Img Data Format set to %s' %cameraTwo.get_imgdataformat())

#create imageBuffers with dequeue
imageBufferOne = deque()
imageBufferTwo = deque()
#create instance of Image to store image data and metadata
img = xiapi.Image()

#start data acquisition
print('Starting data acquisition...')
cameraOne.start_acquisition()
try:
    print('Starting video. Press CTRL+C to exit.')
    t0 = time.time()
    startTime = t0
    prevFrame = 0
    intFrame = cameraOne.get_framerate()
    while True:
        #get data and pass them from camera to img, wait 10s for possible signals
        cameraOne.get_image(img,timeout = 10000)
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
        if (len(imageBufferOne) == queueTime*int(cameraOne.get_framerate())):
            removed = imageBufferOne.popleft()
        #Add tuple of image frame, date time, and numpy array of image
        imageBufferOne.append(imgTup.ImageTuple(img.nframe,datetime.datetime.now(),data))
        cv2.imshow('XiCAM %s' % cameraOne.get_device_name(), data)
        cv2.waitKey(1)
except KeyboardInterrupt:
    cv2.destroyAllWindows()
#stop data acquisition
print('Stopping acquisition...')
cameraOne.stop_acquisition()

print ("Available Bandwidth for camera 1: %s " % cameraOne.get_available_bandwidth())
print ("Available Bandwidth for camera 2: %s " % cameraTwo.get_available_bandwidth())

print("Lag between start of program and start of acquisition: %s" % str(t0 - init_time))
print("Total Acquisition Time: %s " % str(time.time() - t0))
print("Total Frames: %d" % img.nframe)
print("Image Buffer Length: %d" % len(imageBufferOne))
print("Image Buffer contains frames from: %d to %d" %(imageBufferOne[0].frameNum,imageBufferOne[len(imageBufferOne) -1].frameNum))
#stop communication
cameraOne.close_device()

print('Done.')
