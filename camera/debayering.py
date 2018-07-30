import os
import h5py 
import cv2

dirname = "trialimgs"

def fnConverter(frame, dt):
    frmNum = frame.split(" ")[1]
    arrayDt = dt.split(" ")[2]
    return "frm%sdt%s" % (frmNum, arrayDt)

def debayerSave(filename):
	nestedDir = dirname + "/" + os.path.splitext(filename)[0]
	if not os.path.isdir(dirname):
	    os.makedirs(dirname)
	if not os.path.isdir(nestedDir):
	    os.makedirs(nestedDir)
	f = h5py.File(filename, 'r')
	for key in f.keys():
	    image = f[key]
	    debayer = cv2.cvtColor(image.value,cv2.COLOR_BAYER_BG2BGR)
	    convertedFn = fnConverter(str(key).split(",")[0],str(key).split(",")[1])
	    cv2.imwrite('%s/imgRGB%s.png' % (nestedDir, convertedFn), debayer)
	f.close()

debayerSave("myfile7.hdf5")