import cv2
import numpy as np

class debugger:
    def __init__(self):
        self.enabled = False
        self.windows = {}
        self.frames = []
        pass


    def addFrame(self, name, frame, func = None, *args):
        if (not self.enabled):
            return
            
        if (func is not None):
            frame = func(frame, *args)

        self.frames.append([name, frame])


    def reset(self):
        if (not self.enabled):
            return

        if (len(self.windows)):
            for window in self.windows:
                self.windows[window] = False # Mark windows as inactive
        
        self.frames = []


    def display(self):
        if (not self.enabled):
            for window in self.windows:
                cv2.destroyWindow(window)
            self.windows = {}

            return

        # Display active windows
        for frame in self.frames:
            self.windows[frame[0]] = True # Mark window as active
            cv2.imshow(frame[0], frame[1])

        # Close any inactive windows
        for window in self.windows:
            if (not self.windows[window]):
                cv2.destroyWindow(window)

    def toggle(self):
        self.enabled = not self.enabled
            
