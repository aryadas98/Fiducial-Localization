import numpy as np
import cv2
import dicom as pdicom
import matplotlib.pyplot as plt

file = '/home/arya/fiducials/datasets/DICOM-MRI/democases/006.dcm'
data = pdicom.read_file(file)

pixelDims = ((int)(data.Rows), (int)(data.Columns))
pixelSpacing = (float(data.PixelSpacing[0]), float(data.PixelSpacing[1]))

x = np.arange(0.0, (pixelDims[0]+1)*pixelSpacing[0], pixelSpacing[0])
y = np.arange(0.0, (pixelDims[1]+1)*pixelSpacing[1], pixelSpacing[1])

ArrayDicom = data.pixel_array
plt.imshow(ArrayDicom,cmap='gray')
plt.show()
