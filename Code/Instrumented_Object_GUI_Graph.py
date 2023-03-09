# Instrumented Object GUI Graph
# Author: Tony Blake
# Date: August 2021
# Notes:
#
# Backend script for Graph in Instrumented Object GUI

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Pipe

def plot_graph_data(graph_data, flushEvent):
    
   # Create figure for plotting
   fig = plt.figure()
   
   plt.xticks(rotation=45, ha='right')
   plt.subplots_adjust(bottom=0.30)
   plt.title('Sensor Data')
   plt.xlabel('Sample number')
   plt.ylabel('Fz (N)')   
   plt.show()
   
   axis = plt.axes(xlim =(0, 500), ylim =(-100, 100)) 
                 
   x = [];
   y = [];
   
   # Set up plot to call animate() function periodically
   ani = animation.FuncAnimation(fig, animate, fargs=(x, y, axis, graph_data, flushEvent), frames = 500, interval = 20, blit = False)                                                                                                    
          
# This function is called periodically from FuncAnimation
def animate(i, xs, ys, axis, g_data, fEvent):
    
   print("Animate function called") 
            
   if(fEvent.is_set()):
       
      xs.append(i)                    
                 
      ys.append(g_data)
      print("Appending g_data")
      
      line, = ax.plot([], [], lw = 2)
   
      # Plot data
      line.set_data(xs, ys)        

      return line,

def flush_data_pipe(dataEvent, graph_data, data_pipe_out, flushEvent):
    
   while(1):            
         
      if(dataEvent.is_set()): 
          
         graph_data = data_pipe_out.recv()
         
         flushEvent.set()

         #print("graph_data: ", graph_data) #debug
         