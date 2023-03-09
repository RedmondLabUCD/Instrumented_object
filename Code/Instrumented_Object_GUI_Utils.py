'''
Class created for the readout of the ATI sensor, inherits from the multiprocessing class
Created by David Cordova Bulens @ University College Dublin
'''
import serial
import time
import multiprocessing
import csv
import numpy as np
class ATIMonitorThread(multiprocessing.Process):
    
    def __init__(   self, 
                    data_q, msg_q, error_q, 
                    dataRecordingEvent,
                    setEvent,
                    stopEvent,
                    biasEvent,
                    endEvent,
                    repeatEvent,
                    port_num,
                    port_baud,
                    port_stopbits=serial.STOPBITS_ONE,
                    port_parity=serial.PARITY_NONE,
                    port_timeout=0.05):
        multiprocessing.Process.__init__(self)
        
        # Create serial port based on class inputs
        self.serial_port = None
        self.serial_arg = dict( port=port_num,
                                baudrate=port_baud,
                                stopbits=port_stopbits,
                                parity=port_parity,
                                timeout=port_timeout)
        # Queues for data transmission across processes
        self.data_q = data_q
        self.error_q = error_q
        self.msg_q = msg_q
        # Events for defning status of the code and trials
        self.dataRecordingEvent = dataRecordingEvent
        self.setEvent = setEvent
        self.stopEvent = stopEvent
        self.biasEvent = biasEvent
        self.endEvent = endEvent
        self.repeatEvent = repeatEvent
        # Flags for file creation and termination
        self.fileIsCreated = False
        self.getTitle = True
        self.fileIsClosed = False
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
        ''' 
        Run function, starts the serial port, and starts reading information from the main process of the instrumented object.
        The code then waits for different events to be flagged by the main proccess.
        It then reads from the ATI sensor and stores the data in an array. The data is also put in a queue for plotting purposes.
        '''
        # Create serial port transmission
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.ftSensorInit()
        except (serial.SerialException, e):
            self.error_q.put(e.message)
            return
        
        # time0 is the initial time of the process
        time0 = time.time()

        while self.alive.is_set():
            ### FILE CREATION ###
            # If file does not exist and setup has been in GUI then create file
            if self.setEvent.is_set() and not self.fileIsCreated:
               if self.getTitle:
                  # Reading data to set file name
                  fileName = self.msg_q.get()
                  experimentName = self.msg_q.get()
                  folderName = self.msg_q.get()
               self.getTitle = False  

            # Read ATI data and set timestamp
            data = self.ati_mini40_data_bank()
            timestamp = time.time()
            # Put force reading in queue for initial plot update
            self.data_q.put((data[0],data[1],data[2],data[3],data[4],data[5], timestamp))
            
            ### BIAS ###
            # If bias button pressed on GUI then bias the ATI, unless a trial is running in which case bias done after trial
            if self.biasEvent.is_set() and not self.dataRecordingEvent.is_set():
                self.serial_port.write(b'SB\r\n') #bias sensor again to ensure correct biasing conditions
                self.serial_port.write(b'QS\r\n') #start reading data
                time.sleep(1)
                #read whatever the sensor gives after sending the previous command, before start reading the data
                i=0;
                while (i==0):
                    lineATI=self.serial_port.readline()
                    dec=lineATI.decode(encoding='latin-1')
                    for character in dec:
                        if character.isdigit():
                            i=1;
                            print('sensor biased')
                self.biasEvent.clear()  

            ### DATA RECORDING ###
            if self.dataRecordingEvent.is_set() and not self.stopEvent.is_set():
                if not self.fileIsCreated:
                    # Create file for data recording
                    if self.repeatEvent.is_set():
                        self.fileIsCreated = True
                        self.repeatNumber = self.repeatNumber + 1 
                        self.txtfilepath = "%s/%s_%s_ft_%i_%i.csv" % (folderName,experimentName,fileName,self.fileNumber,self.repeatNumber)   
                    else:
                        self.fileNumber = self.fileNumber+1
                        self.fileIsCreated = True
                        self.txtfilepath = "%s/%s_%s_ft_%i.csv" % (folderName,experimentName,fileName,self.fileNumber)          
                    self.fileHandle = open(self.txtfilepath,"w",newline='')
                    self.writer = csv.writer(self.fileHandle,delimiter=',')
                    print("Writing file header...\n")    
                    self.writer.writerow(["Time","fx","fy","fz","tx","ty","tz"]) 
                else:
                    # Start storing data in the np array
                    self.fileIsClosed = False
                    self.trial_data[self.iteration,0] = timestamp
                    self.trial_data[self.iteration,1:] = data
                    
                self.iteration = self.iteration+1

            ### END OF TRIAL ###
            if self.stopEvent.is_set() and not self.fileIsClosed:
               self.writer.writerows(self.trial_data)
               self.fileHandle.close()
               self.trial_data = np.zeros((50000,7))*np.NAN
               self.iteration = 0
               self.fileIsCreated = False
               self.fileIsClosed = True
               print("Finished acquiring data")

               
        # clean up
        if self.serial_port:
            print('here')
            self.serial_port.write(b'\r\n')
            self.serial_port.close()

    def join(self, timeout=None):
        self.alive.clear()
        multiprocessing.Process.join(self, timeout)
    
    def ftSensorInit(self):
        # This function start the communication with the ATI force controller,
        # it then sends information to the controller to set the frequency of
        # the data sampling that is desired and then queries data.
        
        self.serial_port.Terminator = 'CR'; #set terminator        
        # We set a sleep time here to allow the system to be correctly initialized
        self.serial_port.write(b'SB\r\n') #bias sensor
        self.serial_port.write(b'SF 1650\r\n') #set sampling frequency so that we get 200 Hz
        time.sleep(1)
        #read whatever the sensor gives after sending the two previous commands
        i=0
        while (i==0):
            lineATI=self.serial_port.readline()
            dec=lineATI.decode(encoding='latin-1')
            for character in dec:
                if character.isdigit():
                    i=1
                    
        print("Biasing F/T sensor\n");

        # Defining the reference frame of the ATI sensor to match with the viewing plate
        self.serial_port.write(b'TF 0\r\n')
        time.sleep(1)
        self.serial_port.write(b'TC 2, Inst, 225, -130, 0, 1800, 0, 1199\r\n')
        time.sleep(1)
        self.serial_port.write(b'TF 2\r\n')
        time.sleep(1)
        self.serial_port.write(b'SB\r\n') #bias sensor again to ensure correct biasing conditions
        self.serial_port.write(b'QS\r\n') #start reading data
        time.sleep(1)
        
        #read whatever the sensor gives after sending the previous command, before start reading the data
        i=0
        while (i==0):
            lineATI=self.serial_port.readline()
            dec=lineATI.decode(encoding='latin-1')
            for character in dec:
                if character.isdigit():
                    i=1
                
    def ati_mini40_data_bank(self):
        # This function reads data from the ATI sensor and transforms it to Ne and Nm
        
        lineATI=self.serial_port.readline() #reading serial port
        
        dec=lineATI.decode()
      
        sp=dec.split(',')
    
        if (len(sp) == 7):
            # If the data is the correct length, compute the forces and torques
            fx = int(sp[1])/200
            fy = int(sp[2])/200
            fz = int(sp[3])/200
            tx = int(sp[4])/8000
            ty = int(sp[5])/8000
            tz = int(sp[6])/8000      
        else:                
            fx = 'Nan'
            fy = 'Nan'
            fz = 0
            tx = 'Nan'
            ty = 'Nan'
            tz = 'Nan'
        data = [fx,fy,fz,tx,ty,tz]
        return data    