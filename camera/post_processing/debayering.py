import os
import h5py 
import cv2

saved_dir = '/media/pns/0e3152c3-1f53-4c52-b611-400556966cd8/trial_imgs/'
path = '/media/pns/0e3152c3-1f53-4c52-b611-400556966cd8/trials/'
trial_fn = '20181016-114126'

def fnConverter(frame, dt):
    frmNum = frame.split(" ")[1]
    arrayDt = dt.split(" ")[2]
    return "frm%sdt%s" % (frmNum, arrayDt)

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
	    convertedFn = fnConverter(str(key).split(",")[0],str(key).split(",")[1])
	    cv2.imwrite('%s/imgRGB%s.png' % (nestedDir, convertedFn), debayer)
	f.close()

debayerSave(trial_fn)