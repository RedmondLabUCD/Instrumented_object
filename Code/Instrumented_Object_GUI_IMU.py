'''
Class created for the readout of the IMU, inherits from the multiprocessing class
Created by David Cordova Bulens @ University College Dublin
'''
import board
import adafruit_bno055
import time
import multiprocessing
import csv
import numpy as np

class IMUMonitorThread(multiprocessing.Process):
    
   def __init__(   self, 
                    data_q, msg_q,
                    setEvent,
                    recordingEvent,
                    stopEvent,
                    repeatEvent):
      multiprocessing.Process.__init__(self)
        
      self.i2c = None
      self.sensor = None
      # Queues for data transmission across processes
      self.data_q = data_q
      self.msg_q = msg_q      
      # Events for defning status of the code and trials
      self.recordingEvent = recordingEvent
      self.setEvent = setEvent
      self.stopEvent = stopEvent
      self.repeatEvent = repeatEvent
      # Flags for file creation and termination
      self.fileIsCreated = False
      self.getTitle = True
      self.fileIsClosed = False
      self.started = False
      # Variable to keep track of trial ongoing
      self.fileNumber = -1
      self.repeatNumber = 0
      # Array creation to store data during trial
      self.trial_data = np.zeros((50000,7))*np.NAN
      self.iteration = 0
      # Event defining the end of the init function
      self.alive = multiprocessing.Event()
      self.alive.set()
        
   def run(self):
         # Creating board readout 
         self.i2c = board.I2C()
         self.sensor = adafruit_bno055.BNO055_I2C(self.i2c)
        
         # Set starting time the clock
         time0 = time.time()

         ### FILE CREATION ###
         while self.alive.is_set():
            if self.setEvent.is_set() and not self.fileIsCreated:
               if self.getTitle:
                  # Opening file for writing
                  fileName = self.msg_q.get()
                  experimentName = self.msg_q.get()
                  folderName = self.msg_q.get()
               self.getTitle = False   

            # Read data
            timestamp = time.time()            
            data = [timestamp,self.sensor.euler[0],self.sensor.euler[1],self.sensor.euler[2],self.sensor.linear_acceleration[0],self.sensor.linear_acceleration[1],self.sensor.linear_acceleration[2]]
              
            ### DATA RECORDING ###
            if self.recordingEvent.is_set() and not self.stopEvent.is_set():
               if not self.fileIsCreated:                  
                    # Create file for data recording
                    if self.repeatEvent.is_set():
                        self.fileIsCreated = True
                        self.repeatNumber = self.repeatNumber + 1 
                        self.txtfilepath = "%s/%s_%s_IMU_%i_%i.csv" % (folderName,experimentName,fileName,self.fileNumber,self.repeatNumber)          
                    else:
                        self.fileNumber = self.fileNumber+1
                        self.fileIsCreated = True
                        self.txtfilepath = "%s/%s_%s_IMU_%i.csv" % (folderName,experimentName,fileName,self.fileNumber)          
                    self.fileHandle = open(self.txtfilepath,"w",newline='')
                    self.writer = csv.writer(self.fileHandle,delimiter=',')
                    print("Writing file header...\n")
                    self.writer.writerow(["Time","Eula1","Eula2","Eula3","linA1","linA2","linA3"])
               else:                  
                  # Start storing data in the np array
                  self.fileIsClosed = False
                  self.trial_data[self.iteration,:] = data
               
               self.iteration = self.iteration+1

            ### END OF TRIAL ###             
            if self.stopEvent.is_set() and not self.fileIsClosed:
               self.writer.writerows(self.trial_data)
               self.fileHandle.close()   
               self.trial_data = np.zeros((50000,7))*np.NAN
               self.iteration = 0       
               self.stopEvent.clear()
               self.fileIsCreated = False
               self.fileIsClosed = True
               print("Finished acquiring data")

   def join(self, timeout=None):
        self.alive.clear()
        multiprocessing.Process.join(self, timeout)


