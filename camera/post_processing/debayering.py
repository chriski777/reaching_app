import os
import h5py 
import cv2

saved_dir = '/home/pns/Desktop/project/camera/data/debayered/'
path = '/home/pns/Desktop/project/camera/data/'
trial_fn = 'trial: 0, 0'

def fnConverter(camids,frameNum, t):
    camid = camids.split(" ")[1]
    frame = frameNum.split(" ")[2]
    time = t.split(" ")[2]
    return "camera: %s, frame: %s,  t: %s" % (camid, frame, time)

def debayerSave(filename):
	nestedDir = saved_dir + os.path.splitext(filename)[0]
	if not os.path.isdir(saved_dir):
	    os.makedirs(saved_dir)
	if not os.path.isdir(nestedDir):
	    os.makedirs(nestedDir)
	f = h5py.File(os.path.join(path, filename), 'r')
	for key in f.keys():
	    image = f[key]
	    debayer = cv2.cvtColor(image.value,cv2.COLOR_BAYER_BG2BGR)
	    convertedFn = fnConverter(str(key).split(",")[0],str(key).split(",")[1],str(key).split(",")[2])
	    cv2.imwrite('%s/%s.png' % (nestedDir, convertedFn), debayer)
	f.close()

debayerSave(trial_fn)