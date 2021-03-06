import PyCapture2
import cv2
import time
import uuid
import math

def print_build_info():
    lib_ver = PyCapture2.getLibraryVersion()
    print('PyCapture2 library version: %d %d %d %d' % (lib_ver[0], lib_ver[1], lib_ver[2], lib_ver[3]))
    print()

def print_camera_info(cam):
    cam_info = cam.getCameraInfo()
    print('\n*** CAMERA INFORMATION ***\n')
    print('Serial number - %d' % cam_info.serialNumber)
    print('Camera model - %s' % cam_info.modelName)
    print('Camera vendor - %s' % cam_info.vendorName)
    print('Sensor - %s' % cam_info.sensorInfo)
    print('Resolution - %s' % cam_info.sensorResolution)
    print('Firmware version - %s' % cam_info.firmwareVersion)
    print('Firmware build time - %s' % cam_info.firmwareBuildTime)
    print()

def enable_embedded_timestamp(cam, enable_timestamp):
    embedded_info = cam.getEmbeddedImageInfo()
    if embedded_info.available.timestamp:
        cam.setEmbeddedImageInfo(timestamp = enable_timestamp)
        if enable_timestamp :
            print('\nTimeStamp is enabled.\n')
        else:
            print('\nTimeStamp is disabled.\n')

def grab_images(cam,threshold = 5000 ,startAt = 100,maskImg=''):
    prev_ts = None
    fgbg = cv2.createBackgroundSubtractorMOG2()
    mask = cv2.imread(maskImg,0)
    totalpixel = cv2.countNonZero(mask)
    i = 0
    cap = False
    tmpNo = 0
    while 1:
        i=i+1
        if i > startAt:
            i=startAt+1

        try:
            image = cam.retrieveBuffer()
        except PyCapture2.Fc2error as fc2Err:
            print('Error retrieving buffer : %s' % fc2Err)
            continue
        
        ts = image.getTimeStamp()
        if tmpNo%5==0 :
            tmpNo = 0

        tmpName = 'tmp{}'.format(tmpNo)    
        tmpNo = tmpNo + 1

        image.save('/tmpramdisk/{}.bmp'.format(tmpName).encode('utf-8'),PyCapture2.IMAGE_FILE_FORMAT.BMP)
        img = cv2.imread('/tmpramdisk/{}.bmp'.format(tmpName),0)


        img_masked = cv2.bitwise_and(img,img,mask = mask)
        

        fgmask = fgbg.apply(img_masked)
        count = cv2.countNonZero(fgmask)

        #font = cv2.FONT_HERSHEY_SIMPLEX
        #cv2.putText(img,'Timestamp [ {:04d} {:04d} {}]'.format(ts.cycleSeconds, ts.cycleCount,count),(20,20), font, .5,(255,255,255),1,cv2.LINE_AA)
        #cv2.imshow('innertube',img)
        #cv2.imshow('fgmask',fgmask)
        ticks = int(time.time()*1000)
        filename=''
          
        
        if (count > threshold) & (i > startAt) :
            if cap == False :
                setNo = uuid.uuid1().hex
                cap = True
            
            filename = '{:04d}-{}-{}'.format(ticks, setNo,count)
            image.save('/vanaramdisk/{}.bmp'.format(filename).encode('utf-8'),PyCapture2.IMAGE_FILE_FORMAT.BMP)
        else:
            cap = False
            
        if prev_ts:
            percent = math.ceil((count/totalpixel) * 100)
            diff = (ts.cycleSeconds - prev_ts.cycleSeconds) * 8000 + (ts.cycleCount - prev_ts.cycleCount)
            print('Timestamp [ {:04d} {:04d} ] - {:03d} - {} {} {}% {}'.format(ticks, ts.cycleCount, diff,totalpixel,count,percent,filename))

        prev_ts = ts

print_build_info()

# Ensure sufficient cameras are found
bus = PyCapture2.BusManager()
num_cams = bus.getNumOfCameras()
print('Number of cameras detected: ', num_cams)
if not num_cams:
    print('Insufficient number of cameras. Exiting...')
    exit()

# Select camera on 0th index
c = PyCapture2.Camera()
uid = bus.getCameraFromIndex(0)
c.connect(uid)
print_camera_info(c)

# Enable camera embedded timestamp
enable_embedded_timestamp(c, True)

print('Starting image capture...')
c.startCapture()
grab_images(c, 50000,300,'./mask/rattler2.png')
c.stopCapture()

# Disable camera embedded timestamp
enable_embedded_timestamp(c, False)
c.disconnect()

input('Done! Press Enter to exit...\n')