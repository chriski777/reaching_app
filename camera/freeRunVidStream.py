from ximea import xiapi
from collections import deque
import ImageTuple as imgTup
import cv2
import time
import datetime

#Minimum trigger period is dependent on exposure time 
exp_per = 6700
#Image Buffer queue in seconds 
queueTime = 5
cameraOne = xiapi.Camera()

#start communication
print('Opening first camera...')
cameraOne.open_device()

#Settings
cameraOne.set_imgdataformat('XI_RGB24')
cameraOne.set_exposure(exp_per)
cameraOne.set_gain(20.0)
cameraOne.set_sensor_feature_value(1)

print('Exposure was set to %i us' %cameraOne.get_exposure())
print('Gain was set to %f db' %cameraOne.get_gain())
print('Img Data Format set to %s' %cameraOne.get_imgdataformat())

#create imageBuffer with dequeue
imageBuffer = deque()

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
        if (len(imageBuffer) == queueTime*int(cameraOne.get_framerate())):
            removed = imageBuffer.popleft()
        #Add tuple of image frame, date time, and numpy array of image
        imageBuffer.append(imgTup.ImageTuple(img.nframe,datetime.datetime.now(),data))
        cv2.imshow('XiCAM %s' % cameraOne.get_device_name(), data)
        cv2.waitKey(1)
except KeyboardInterrupt:
    cv2.destroyAllWindows()
#stop data acquisition
print('Stopping acquisition...')
cameraOne.stop_acquisition()

print("Total Acquisition Time: %s " % str(time.time() - t0))
print("Total Frames: %d" % img.nframe)
print("Image Buffer Length: %d" % len(imageBuffer))
print("Image Buffer contains frames from: %d to %d" %(imageBuffer[0].frameNum,imageBuffer[len(imageBuffer) -1].frameNum))
#stop communication
cameraOne.close_device()

print('Done.')
