'''
Class created for the readout of the camera, inherits from the multiprocessing class
Created by David Cordova Bulens @ University College Dublin
'''
from picamera import PiCamera
import time
from gpiozero import LED
import time
import multiprocessing

class CameraMonitorThread(multiprocessing.Process):
    
    def __init__(   self,
                    cameraSetupEvent, 
                    recordingEvent,
                    previewEvent,
                    stopEvent,
                    repeatEvent,
                    msgQueue,
                    led0,
                    led1):
        multiprocessing.Process.__init__(self)
        
        self.i2c = None
        self.sensor = None

        self.camera = None
        self.msgQueue = msgQueue        
        # Events for defning status of the code and trials
        self.cameraSetupEvent = cameraSetupEvent
        self.recordingEvent = recordingEvent
        self.previewEvent = previewEvent
        self.stopEvent = stopEvent
        self.repeatEvent = repeatEvent
        # Flags for file creation and termination
        self.previewIsOn = False
        self.fileIsCreated = False
        self.started = False
        # Creating leds for synchronization
        self.led0 = led0
        self.led1 = led1
        # Array creation to store data during trial
        self.repeatNumber = 0        
        self.trial_data = np.zeros((50000,1))*np.NAN
        # Event defining the end of the init function
        self.alive = multiprocessing.Event()
        self.alive.set()
                
        
    def run(self):
        ''' 
        Run function, starts the camera port, and starts reading information from the main process of the instrumented object.
        The code then waits for different events to be flagged by the main proccess.
        It then reads from the Camera and stores the data in an array. 
        '''
        ### CREATING CAMERA ###
        if self.camera: 
            self.camera.close()   
        self.camera = PiCamera()
        self.camera.color_effects = (128,128) # Setting it to grayscale     

        ### WAITING FOR SETUP TO BE DONE IN THE GUI ###
        e_wait = self.cameraSetupEvent.wait(); # Waiting for the setup event
    
        ### CREATING FILE NAME ###
        if e_wait:
            # Once the setup event is set we read the camera parameters
            fps = self.msgQueue.get()
            resolution = self.msgQueue.get()
            fileName = self.msgQueue.get()
            experimentName = self.msgQueue.get()
            folderName = self.msgQueue.get()
            self.camera.resolution = resolution
            self.camera.framerate = fps
            self.videoNumber = -1
            self.timeStamp = -1
            self.N_frames = 0
            print('Camera information set')
    
        # Initialize time
        time0 = time.time()
        timeStamp = -1
        N_frames = 0

        while self.alive.is_set():
            ### PREVIEW WINDOW ###
            if self.previewEvent.is_set():
                if not self.previewIsOn:
                    self.camera.start_preview(fullscreen = False, window = [100,20,640,480]);
                    self.previewIsOn = True
                    self.previewEvent.clear()
                else:
                    self.camera.stop_preview()
                    self.previewIsOn = False
                    self.previewEvent.clear()

            ### DATA RECORDING ###
            if self.recordingEvent.is_set() and not self.stopEvent.is_set():
                self.started = True
                if self.fileIsCreated:
                    # Reading timestamp of current frame
                    timeStamp_tmp = self.camera.frame.timestamp
                    if timeStamp_tmp != timeStamp and timeStamp_tmp !=None:
                        timeStamp = timeStamp_tmp
                        self.trial_data[N_frames] = timeStamp
                        # self.fileHandle.write(str(timeStamp))
                        # self.fileHandle.write('\n')
                        N_frames = N_frames +1  
                    if N_frames == 30:
                        self.led0.on()
                        self.led1.on()
                    if N_frames == 60:            
                        self.led0.off()
                        self.led1.off()
                else:                    
                    if self.repeatEvent.is_set():
                        print('video repeat')
                        self.repeatNumber = self.repeatNumber + 1 
                        txtFilePath = "%s/%s_%s_Camera_%i_%i.txt" % (folderName,experimentName,fileName,self.videoNumber,self.repeatNumber)
                        videoFilePath = "%s/%s_%s_%i_%i.h264" % (folderName,experimentName,fileName,self.videoNumber,self.repeatNumber)
                        self.fileHandle = open(txtFilePath,"w");  
                        self.startTime = time.time()
                    else:                        
                        self.videoNumber = self.videoNumber +1
                        txtFilePath = "%s/%s_%s_Camera_%i.txt" % (folderName,experimentName,fileName,self.videoNumber)
                        videoFilePath = "%s/%s_%s_%i.h264" % (folderName,experimentName,fileName,self.videoNumber)
                        self.fileHandle = open(txtFilePath,"w");  
                        self.startTime = time.time()
                    print('starting recording\n')
                    self.camera.start_recording(videoFilePath,format='h264')
                    self.fileIsCreated = True

            if self.stopEvent.is_set() and self.started:                
               self.writer.writerows(self.trial_data)
                if self.camera.recording:
                    self.camera.stop_recording()
                self.recordingEvent.clear()
                N_frames = 0
                self.fileIsCreated = False
                self.started = False
                self.fileHandle.close()
                timeStamp = -1
            
            
        # clean up
        if self.camera:
            self.camera.close()

    def join(self, timeout=None):
        self.alive.clear()
        multiprocessing.Process.join(self, timeout)

    
