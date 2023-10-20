# InOB #

InOb CAD files and python code for data acquisition.

### What does this repository contain ###

* CAD_files: Contains all the parts forming the InOb in STL and F3D formats. These can be printed in any 3d printer.
* Code: Contains all the acquisition code necessary to run a GUI allowing for synchronized data acquisition from InOb using a raspberry pi 4B.

### Setup ###

#### Python installation ####
To run the acquisition code you will need to create a virtual environment and install all packages in requirements.txt.

<code> pip install --r requirements.txt </code>

As for PyQt5, you should follow the explanations given in https://github.com/tranter/raspberry-pi-qt-builds.

Once PyQt5 is installed, you can link it to your virtual environment by doing:

<code> pip install vext.pyqt5 </code>

#### Running the code ####

To run the GUI just execute the following line in the folder where the code is stored

<code> python Instrumented_Object_GUI.py </code>

This will prompt up the GUI. In the GUI the following steps should be followed:

* Setup the ID of the participant you will be testing with the object.
* Setup the folder the data will be saved to.
* Setup the camera resolution and framerate.
* Click the save setup button. 

Once those steps have been followed, the user can:

* Preview the camera image to adjust the focus.
* Test the two synchronisation LEDs are properly working.
* Start a trial.
* Stop a trial.

### Contact ###

If you have any questions you can send them to david.cordovabulens@ucd.ie or stephen.redmond@ucd.ie