# The program draws all DICOM images stored
# in a directory sequentially.

import numpy as np
import cv2
import dicom as pdicom
import matplotlib.pyplot as plt
import os
import sys

PATH = sys.argv[1] # get the path

files = os.listdir(PATH)
files.sort()

fig = None
for file in files:
    dicomfile = pdicom.read_file(os.path.join(PATH,file))
    img = dicomfile.pixel_array
    if fig is None:
        fig = plt.imshow(img,cmap='gray')
    else:
        fig.set_data(img)
    plt.pause(0.5)
    plt.draw()
