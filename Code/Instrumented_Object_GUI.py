# # Instrumented Object GUI
# # Authors: Tony Blake, David Cordova
# # Date: August 2021
# # Note: see git repo for commit history 

import random, sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import PyQt5.QtWidgets as QtWidgets
import pyqtgraph as pg
import queue
from random import randint
#from ComMonitor import ComMonitorThread
import serial
import time
import os
import csv
#from multiprocessing import Process, Event, Queue, Pipe
import multiprocessing
import threading
from picamera import PiCamera
from gpiozero import LED
from Instrumented_Object_GUI_IMU import IMUMonitorThread
from Instrumented_Object_GUI_Utils import ATIMonitorThread
from Instrumented_Object_GUI_Camera import CameraMonitorThread

class DataMonitor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Creating all the required processes and events for the different processes that will run in parallel
        self.ATIData_q          = multiprocessing.Queue()
        self.ATIMsg_q           = multiprocessing.Queue()
        self.ATIError_q         = multiprocessing.Queue()
        self.IMUData_q          = multiprocessing.Queue()
        self.IMUMsg_q           = multiprocessing.Queue()
        self.cameraMsg_q        = multiprocessing.Queue()

        self.dataRecordingEvent = multiprocessing.Event()
        self.setEvent           = multiprocessing.Event()
        self.stopEvent          = multiprocessing.Event()
        self.biasEvent          = multiprocessing.Event()
        self.endEvent           = multiprocessing.Event()
        self.previewEvent       = multiprocessing.Event()
        self.repeatEvent        = multiprocessing.Event()
        
        self.led0 = LED(23)
        self.led1 = LED(24)

        self.ATIMonitor         = ATIMonitorThread(self.ATIData_q,
                                self.ATIMsg_q,
                                self.ATIError_q,
                                self.dataRecordingEvent,
                                self.setEvent,
                                self.stopEvent,
                                self.biasEvent,
                                self.endEvent,
                                self.repeatEvent,
                                "/dev/ttyUSB0",
                                115200)
        
        self.IMUMonitor         = IMUMonitorThread(self.IMUData_q, self.IMUMsg_q,
                                self.setEvent,
                                self.dataRecordingEvent,
                                self.stopEvent,
                                self.repeatEvent)

        self.CameraMonitor      = CameraMonitorThread(self.setEvent,
                                self.dataRecordingEvent,
                                self.previewEvent,
                                self.stopEvent,
                                self.cameraMsg_q,
                                self.led0,
                                self.led1)

        self.ATIMonitor.start()
        self.IMUMonitor.start()
        self.CameraMonitor.start()

        # Creating graphical interfaces
        self.title = 'Instrumented object graphical interface'
        self.left = 50
        self.top = 50
        self.width = 780
        self.height = 320
        self.trialNumber = 0
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.ATIx = list(range(100))  # 100 time points
        self.ATIy = [randint(0,100) for _ in range(100)]  # 100 data points
        self.IMUx = list(range(100))  # 100 time points
        print(self.IMUx[1:])
        self.IMUy = [randint(0,100) for _ in range(100)]  # 100 data points
        self.IMUtime = 0
        self.IMUdata = 0
        self.ATItime = 0
        self.ATIdata = 0
        self.pen = pg.mkPen(color=(255, 0, 0))
        self.forcePen = pg.mkPen(color=(255,255,0))
        self.initUI()
        # ... init continued ...
        self.timer = QTimer()
        #self.timer.setInterval(0.5)
        self.timer.timeout.connect(self.updatePlotData)
        self.timer.start()
        self.show()

    def get_all_from_queue(self,Q):
        """ Empties queue of data
        """
        try:
            while True:
                yield Q.get_nowait( )
        except queue.Empty:
            return

    def read_ATI_data(self):
        """ Called periodically by the update timer to read data
            from the ATI process.
        """
        qdata = list(self.get_all_from_queue(self.ATIData_q))

        if len(qdata) > 0:
            self.ATIdata = qdata[-1][2]
            self.ATItime = qdata[-1][6]

    def read_IMU_data(self):
        """ Called periodically by the update timer to read data
            from the ATI process.
        """
        qdata = list(self.get_all_from_queue(self.IMUData_q))

        if len(qdata) > 0:
            self.IMUdata = qdata[-1][6]
            self.IMUtime = qdata[-1][0]

    def initUI(self):
        ''' Initializing the GUI interface '''
        widget = QtWidgets.QWidget()        
        
        experimentIDLabel = QtWidgets.QLabel('Experiment ID')        
        self.experimentIDTextbox = QtWidgets.QLineEdit(self)

        participantIDLabel = QtWidgets.QLabel('Participant ID')        
        self.participantIDTextbox = QtWidgets.QLineEdit(self)
        
        self.folderLabel = QtWidgets.QLabel('Folder')
        self.folderTextbox = QtWidgets.QLineEdit(self)
        self.folderSelectionButton = QtWidgets.QPushButton('...', self)
        self.folderSelectionButton.clicked.connect(self.folderSelect)   

        self.previewCheckBox = QtWidgets.QCheckBox('Camera preview')
        self.previewCheckBox.toggled.connect(lambda:self.previewCamera(self.previewCheckBox))

        self.cameraParam = QtWidgets.QComboBox(self)
        cameraParamList = ["1280x720/60fps", "1920x1080/30fps"]
        self.cameraParam.addItems(cameraParamList)
        
        self.led0Test = QtWidgets.QCheckBox('Led 0 test')
        self.led0Test.toggled.connect(lambda:self.led0Toggle(self.led0Test))
        
        self.led1Test = QtWidgets.QCheckBox('Led 1 test')
        self.led1Test.toggled.connect(lambda:self.led1Toggle(self.led1Test))
                
        self.setupButton = QtWidgets.QPushButton('Save setup', self)
        self.setupButton.clicked.connect(self.setup)   
                
        self.startButton = QtWidgets.QPushButton('Start trial', self)
        self.startButton.clicked.connect(self.startButtonAction) 

        self.stopButton = QtWidgets.QPushButton('Stop trial', self)
        self.stopButton.clicked.connect(self.stopButtonAction)
        
        self.biasButton = QtWidgets.QPushButton('Bias ATI', self)
        self.biasButton.clicked.connect(self.biasButtonAction) 

        self.ATIWindowPlot = pg.PlotWidget(title='z Force [N]')
        self.ATIWindowPlot.setBackground('k') 
        self.ATIDataLine =  self.ATIWindowPlot.plot(self.ATIx, self.ATIy, pen=self.pen)
        
        self.IMUWindowPlot = pg.PlotWidget(title='y Acceleration')
        self.IMUWindowPlot.setBackground('k')  
        self.IMUDataLine =  self.IMUWindowPlot.plot(self.IMUx, self.IMUy, pen=self.pen)
        
        layout = QtWidgets.QGridLayout() 
        widget.setLayout(layout)  

        layout.addWidget(experimentIDLabel,1,0)
        layout.addWidget(self.experimentIDTextbox,1,1,1,2)
        layout.addWidget(participantIDLabel,2,0)
        layout.addWidget(self.participantIDTextbox,2,1,1,2)
        layout.addWidget(self.folderLabel,0,0)
        layout.addWidget(self.folderTextbox,0,1)
        layout.addWidget(self.folderSelectionButton,0,2)
        layout.addWidget(self.previewCheckBox,3,0)
        layout.addWidget(self.cameraParam,3,1)
        layout.addWidget(self.setupButton,4,0)
        layout.addWidget(self.led0Test,5,0)
        layout.addWidget(self.led1Test,5,1)
        layout.addWidget(self.startButton,6,0)
        layout.addWidget(self.stopButton,6,1)
        layout.addWidget(self.biasButton,6,2)
        layout.addWidget(self.ATIWindowPlot,0,3,2,6)
        layout.addWidget(self.IMUWindowPlot,2,3,2,6)
        #layout.setColumnStretch(3,3)
        self.setCentralWidget(widget)

    def folderSelect(self):
        self.selectedDir = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Choose Directory', directory=os.getcwd())
        self.folderTextbox.setText(self.selectedDir)

    def previewCamera(self,b):
        self.previewEvent.set()

        
    def led0Toggle(self,b):
        if b.isChecked():
            self.led0.on()
        else:
            self.led0.off()
            
    def led1Toggle(self,b):
        if b.isChecked():
            self.led1.on()
        else:
            self.led1.off()


    def setup(self):
        if self.participantIDTextbox.text() == "":
            QtWidgets.QMessageBox.warning(self, 'Message', "No participant ID entered")
            self.participantIDTextbox.setFocus()
            return False

        if self.folderTextbox.text() == "":
            QtWidgets.QMessageBox.warning(self, 'Message', "No folder selected")
            self.folderTextbox.setFocus()
            return False

        if self.experimentIDTextbox.text() == "":
            QtWidgets.QMessageBox.warning(self, 'Message', "No experiment ID entered")
            self.experimentIDTextbox.setFocus()
            return False

        experimentID = self.experimentIDTextbox.text()
        participantID = self.participantIDTextbox.text()
        folderName = self.folderTextbox.text()    
        cameraParam = self.cameraParam.currentText()
        cameraParam = cameraParam.split("/")
        fps = cameraParam[-1]
        fps = fps.split("f")[0]
        resolution = cameraParam[0]
        resolution = resolution.split("x")
        resolution = (int(resolution[0]),int(resolution[1]))

        self.cameraMsg_q.put(int(fps))
        self.cameraMsg_q.put(resolution)
        self.cameraMsg_q.put(participantID)
        self.cameraMsg_q.put(experimentID)
        self.cameraMsg_q.put(folderName)   
        
        self.ATIMsg_q.put(participantID)
        self.ATIMsg_q.put(experimentID)
        self.ATIMsg_q.put(folderName)

        self.IMUMsg_q.put(participantID)
        self.IMUMsg_q.put(experimentID)
        self.IMUMsg_q.put(folderName)

        self.setEvent.set()

    def startButtonAction(self):
        if not self.setEvent.is_set():
            QtWidgets.QMessageBox.warning(self, 'Message', "Setup has not been registered correctly")
            return
        else:
            self.stopEvent.clear()
            self.dataRecordingEvent.set()
            self.reply = QtWidgets.QMessageBox.information(self, 'Message', "Recording started")

    def stopButtonAction(self):
        if not self.dataRecordingEvent.is_set():
            QtWidgets.QMessageBox.warning(self, 'Message', "Trial has not been started")
            return
        else:
            self.stopEvent.set()
            
    def biasButtonAction(self):
        self.biasEvent.set()

    def updateATIPlot(self):
        self.read_ATI_data()
        if self.ATItime:
            #print(self.ATItime)
            self.ATIx = self.ATIx[1:]
            self.ATIx.append(self.ATItime)

        if self.ATIdata:
            self.ATIy = self.ATIy[1:]
            self.ATIy.append(self.ATIdata)

        self.ATIDataLine.setData(self.ATIx,self.ATIy)

        
    def updateIMUPlot(self):
        self.read_IMU_data()
        if self.IMUtime:
            self.IMUx = self.IMUx[1:]
            self.IMUx.append(self.IMUtime)
        
        if self.IMUdata:
            self.IMUy = self.IMUy[1:]
            self.IMUy.append(self.IMUdata)
        self.IMUDataLine.setData(self.IMUx,self.IMUy)

    def updatePlotData(self):
        self.updateIMUPlot()
        self.updateATIPlot()

    def closeEvent(self,event):
        if self.ATIMonitor is not None:
            print('closing ATI process')
            self.ATIMonitor.join()
            self.ATIMonitor.close()

        if self.IMUMonitor is not None:
            print('closing IMU process')
            self.IMUMonitor.join()
            self.IMUMonitor.close()

        if self.CameraMonitor is not None:
            print('closing camera process')
            self.CameraMonitor.join()
            self.CameraMonitor.close()
            
        can_exit = True    
        if can_exit:
            event.accept() # let the window close
        else:
            event.ignore()
        

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = DataMonitor()
    sys.exit(app.exec_())

