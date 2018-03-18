import os
import dicom
import cv2
import mritopng
import matplotlib.pyplot as plt
import numpy as np
from math import sqrt
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

def doNothing():
    print("i do nothing")
lst=[]
def browseFunc(ls=lst):
    fname = filedialog.askdirectory()
    ls+=[fname]
alst=[]
def abrowseFunc(ls=alst):
    fname = filedialog.askdirectory()
    ls+=[fname]


def acrelicfunc(ls=alst):
    fname = ls[0]
    dcmfile = []
    dcmlist = []
    fiducoords = []
    voxeli = []
    mritopng.convert_folder(fname,fname + '/png')
    os.chdir(fname)
    for file in os.listdir():
        if 'png' not in file.lower():
            dcmlist.append(dicom.read_file(file))
        else:
            pass
    pnglist = []
    os.chdir(fname + '\png')
    for file in os.listdir():
        pnglist.append(file)
    # pnglist.pop()
    for file in pnglist:
        img = cv2.imread(file, 0)
        orig = img.copy()
        shape = img.shape
        _, img = cv2.threshold(img, 195, 255, cv2.THRESH_BINARY)
        _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objs = list(filter(lambda x: cv2.contourArea(x) > 800, contours))

        if img is not None:
            img.fill(0)
        else:
            img = np.zeros(shape, np.uint8)

        if len(objs) == 1 and cv2.contourArea(objs[0]) > 3000:  # side view
            # print("Block")
            obj = objs[0]
            approx = cv2.approxPolyDP(obj, 0.02 * cv2.arcLength(obj, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            img = cv2.drawContours(img, [obj], 0, 1, -1)
            img[y - 2:y + h + 2, x - 2:x + w + 2] = 0

            _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            boxes = [cv2.boundingRect(cnt) for cnt in contours]
            boxes = list(filter(lambda x: x[2] * x[3] < 200 and x[2] * x[3] > 20, boxes))

            vert_groups = []
            horz_groups = []
            for i in range(0, len(boxes) - 1):
                for j in range(i + 1, len(boxes)):
                    x1, y1, _, _ = boxes[i]
                    x2, y2, _, _ = boxes[j]
                    dist_x = abs(x1 - x2)
                    dist_y = abs(y1 - y2)
                    if dist_x > 20 and dist_x < 40 and dist_y < 5:
                        horz_groups.append((boxes[i], boxes[j]))
                    elif dist_y > 20 and dist_y < 40 and dist_x < 5:
                        vert_groups.append((boxes[i], boxes[j]))

            fids = []
            for group in horz_groups:
                x1, y1, w1, _ = group[0]
                x2, y2, w2, _ = group[1]
                gap_dist = min(abs(x2 - x1 - w1), abs(x1 - x2 - w2))
                if gap_dist >= 15:
                    fids.append(((x1 + x2 + gap_dist) // 2, (y1 + y2) // 2))

            for group in vert_groups:
                x1, y1, _, h1 = group[0]
                x2, y2, _, h2 = group[1]
                gap_dist = min(abs(y2 - y1 - h1), abs(y1 - y2 - h2))
                if gap_dist >= 15:
                    fids.append(((x1 + x2) // 2, (y1 + y2 + gap_dist) // 2))

        else:  # either top view or noise
            # print("Circles")
            fids = []
            for obj in objs:
                (x, y), r = cv2.minEnclosingCircle(obj)
                actual_area = cv2.contourArea(obj)
                ideal_area = 3.14 * r * r
                perc_filled = actual_area / ideal_area
                if r > 10 and r < 35 and perc_filled > 0.9:
                    fids.append((int(x), int(y)))

        print(str(len(fids)) + " fiducials detected.")
        print(fids)
        print(file)
        if len(fids) != 0:
            print(file)
            ds = dcmlist[pnglist.index(file)]
            vector = ds.ImageOrientationPatient
            pixelsize = ds.PixelSpacing
            voxel = ds.ImagePositionPatient
            for k in fids:
                if abs(vector[0]) == 1:
                    if abs(vector[4]) == 1:
                        x = k[0]
                        y = k[1]
                        plane = 'xy'
                        voxelx = voxel[0] + vector[0] * pixelsize[0] * x
                        voxely = voxel[1] + vector[4] * pixelsize[1] * y
                        voxelz = voxel[2]
                    else:
                        x = k[0]
                        z = k[1]
                        plane = 'xz'
                        voxelx = voxel[0] + vector[0] * pixelsize[0] * x
                        voxely = voxel[1]
                        voxelz = voxel[2] + vector[5] * pixelsize[1] * z
                else:
                    y = k[0]
                    z = k[1]
                    plane = 'yz'
                    voxelx = voxel[0]
                    voxely = voxel[1] + vector[1] * pixelsize[1] * y
                    voxelz = voxel[2] + vector[5] * pixelsize[0] * z

                print(plane, (voxelx, voxely, voxelz))
                fiducoords.append((voxelx, voxely, voxelz))
                voxeli.append(voxelx)

    print(fiducoords)
    print(len(fiducoords))
    correct = []
    for i in fiducoords:
        check = True
        for j in fiducoords[fiducoords.index(i):]:
            dist1 = abs((i[0] - j[0]))
            dist2 = abs(i[1] - j[1])
            dist3 = abs((i[2] - j[2]))
            if dist1 < 1 and dist2 < 1 and dist3 < 1:
                check = False

        if check:
            correct.append(i)
    print(len(fiducoords), fiducoords)
    print(len(correct), correct)
    for(a,b,c) in correct:
        print (sqrt(a*a + b*b + c*c))


    def getKey(item):
        return fiducoords[0]


    sorted(fiducoords, key=getKey)
    print(fiducoords)


                                                                                
    
def mainFunc(ls=lst):
    for fname in ls:
        print(fname)
        mritopng.convert_folder(fname, fname + '/png')
        dcmfile = []
        dcmlist = []
        fiducoords = []
        os.chdir(fname)
        for file in os.listdir():
            if 'png' not in file.lower():
                dcmlist.append(dicom.read_file(file))
            else:
                pass
        pnglist = []
        os.chdir(fname+'/png')
        for file in os.listdir():
            pnglist.append(file)
        pnglist.pop()
        for file in pnglist:
            img = cv2.imread(file, 0)
            # The algorithm is good for images of size 256x256. So we have to scale
            # the input image down, and then scale the result back up.
            dimensions = img.shape
            scale = dimensions[0] // 256
            img = cv2.resize(img, (256, 256))    

            # Skull detection
            copy = img.copy()
            img = cv2.medianBlur(img, 5)
            img = cv2.inRange(img, 20, 255)
            _, contours, _ = cv2.findContours(img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            skull = max(contours, key=cv2.contourArea)
            M = cv2.moments(skull)
            skull_cent = (M['m10'] // M['m00'], M['m01'] // M['m00'])
            mask = cv2.drawContours(np.zeros(img.shape), [skull], 0, 1, 20)
            mask = np.uint8(mask)
            img = cv2.multiply(copy, mask)

            # Detect points that are outside the head,
            # but close to the bones of the skull
            img_diag = (img.shape[0]**2 + img.shape[1]**2)**0.5
            img = cv2.linearPolar(img, skull_cent, img_diag, cv2.WARP_FILL_OUTLIERS)
            img = cv2.inRange(img, 120, 255)

            _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            bones = [cnt for cnt in contours if cv2.contourArea(cnt) > 30]

            img = np.uint8(cv2.drawContours(np.zeros(copy.shape), bones, -1, 1, -1))
            temp = cv2.reduce(img, 0, cv2.REDUCE_MAX)
            temp = cv2.findNonZero(temp)
            leftmost = temp[temp[:, :, 0].argmin()][0][0]
            rightmost = temp[temp[:, :, 0].argmax()][0][0]

            mask = np.zeros(copy.shape, np.uint8)
            for row in range(img.shape[0]):
                for column in range(rightmost, leftmost, -1):
                    if img[row, column] != 0:
                        mask[row, column + 2:column + 15] = 1
                        break

            mask = cv2.linearPolar(mask, skull_cent, img_diag, cv2.WARP_INVERSE_MAP)
            img = cv2.multiply(copy, mask)

            img = cv2.inRange(img, 160, 255)

            # Group nearby points and print output
            _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            cents = []
            for cnt in contours:
                M = cv2.moments(cnt)
                if (M['m00'] != 0):
                    cents.append((M['m10'] // M['m00'], M['m01'] // M['m00']))
                else:
                    cents.append(tuple(cnt[0][0]))

            groups = []
            for pnt1 in cents:
                added = False
                for group in groups:
                    if not added:
                        for pnt2 in group:
                            approx_dist = abs(pnt1[0] - pnt2[0]) + abs(pnt1[1] - pnt2[1])
                            if approx_dist < 25:
                                group.append(pnt1)
                                added = True
                                break
                if not added:
                    groups.append([pnt1])

            fiducials = []
            for group in groups:
                sum = (0, 0)
                for pnt in group:
                    sum = (sum[0] + pnt[0], sum[1] + pnt[1])
                sum = (int(sum[0] / len(group)), int(sum[1] / len(group)))
                fiducials.append(sum)

            output = copy.copy()
            for pnt in fiducials:
                cv2.circle(output, pnt, 10, 255, 2)

            # Resize the image back to thr original dimensions before grouping
            output = cv2.resize(output, dimensions)

            # Scale up the coordinates of the fiducials
            temp = np.multiply(fiducials, 2)
            fiducials = [tuple(x) for x in temp]

            #print(str(len(fiducials)), " Fiducials detected:")
            #print(fiducials)

            if len(fiducials) != 0:
                print(file)
                ds = dcmlist[pnglist.index(file)]
                vector = ds.ImageOrientationPatient
                pixelsize = ds.PixelSpacing
                voxel = ds.ImagePositionPatient
                for k in fiducials:
                    if abs(vector[0]) == 1:
                        if abs(vector[4]) == 1:
                            x = k[0]
                            y = k[1]
                            plane = 'xy'
                            voxelx = voxel[0] + vector[0] * pixelsize[0] * x
                            voxely = voxel[1] + vector[4] * pixelsize[1] * y
                            voxelz = voxel[2]
                        else:
                            x = k[0]
                            z = k[1]
                            plane = 'xz'
                            voxelx = voxel[0] + vector[0] * pixelsize[0] * x
                            voxely = voxel[1]
                            voxelz = voxel[2] + vector[5] * pixelsize[2] * z
                    else:
                        y = k[0]
                        z = k[1]
                        plane = 'yz'
                        voxelx = voxel[0]
                        voxely = voxel[1] + vector[1] * pixelsize[1] * y
                        voxelz = voxel[2] + vector[5] * pixelsize[0] * z

                    #print(plane, (voxelx, voxely, voxelz))
                    fiducoords.append((voxelx, voxely, voxelz))
    # iske pehle ka code for all 3 planes, iske baad ka code bas ek baar chlna h last me
    # below is the code for elimination of fidu
    finalfidu = 0
    count = 0
    captainswing=[]
    print(fiducoords)
    fiducoords = sorted(fiducoords, key=lambda x: x[0])
    correct = []
    a = [fiducoords[0]]
    for i in fiducoords:
        check = True
        for j in fiducoords[fiducoords.index(i) + 1:]:
            dist1 = abs((i[0] - j[0]))
            dist2 = abs(i[1] - j[1])
            dist3 = abs((i[2] - j[2]))
            if dist1 < 3 and dist2 < 3 and dist3 < 3:
                print(fiducoords.index(j))
                check = False
                break

        if check:
            correct.append(i)
    print(len(fiducoords), fiducoords)

    # print(fiducoords)
    for(a,b,c) in correct:
        print (sqrt(a*a + b*b + c*c))

def countFidu():

    mainFunc()
    y = mainFunc()
    print (y.finalfidu)
    

def findCoord():

    mainFunc()
    z = mainFunc()
    print (y.fiducoords)
    

#************************************************************************************************************


    

LARGE_FONT= ("Verdana", 12)


class SeaofBTCapp(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Fiducials Localisation")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, realSkull, phantomSkull):

            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

        
class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)

        label = tk.Label(self, text="Start Page", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Real Skull", command=lambda: controller.show_frame(realSkull))
        button1.pack()

        button2 = ttk.Button(self, text="Phantom Skull", command=lambda: controller.show_frame(realSkull))
        button2.pack()

        button3 = ttk.Button(self, text="Acrelic1", command=lambda: controller.show_frame(phantomSkull))
        button3.pack()

        button4 = ttk.Button(self, text="Acrelic2", command=lambda: controller.show_frame(realSkull))
        button4.pack()

        button5 = ttk.Button(self, text="Glass Scan", command=lambda: controller.show_frame(realSkull))
        button5.pack()


class realSkull(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Real!", font=LARGE_FONT)
        label.grid()

        label_1 = tk.Label(self, text='Axial Plane')
        browse_1= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_1 = tk.Entry(self)

        label_2 = tk.Label(self, text='Coronal Plane')
        browse_2= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_2 = tk.Entry(self)

        label_3 = tk.Label(self, text='Sagittal Plane')
        browse_3= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_3 = tk.Entry(self)
        
        label_1.grid(row=2, sticky="E")
        entry_1.grid(row=2, column=1)
        browse_1.grid(row=2, column=2)

        label_2.grid(row=3)
        entry_2.grid(row=3, column=1)
        browse_2.grid(row=3, column=2)

        label_3.grid(row=4)
        entry_3.grid(row=4, column=1)
        browse_3.grid(row=4, column=2)

        count = ttk.Button(self, text='Count Fiducials', command=mainFunc)
        coord = ttk.Button(self, text='Show Coordinates', command=mainFunc)

        count.grid(columnspan=2)
        coord.grid(columnspan=2)
        
        button1 = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(StartPage))
        button1.grid()

        button2 = ttk.Button(self, text="Phantom Skull", command=lambda: controller.show_frame(phantomSkull))
        button2.grid()
        
class phantomSkull(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="ACRELIC!", font=LARGE_FONT)
        label.grid()

        label_1 = tk.Label(self, text='Input File')
        browse_1= ttk.Button(self, text = "Browse", command = abrowseFunc, width = 10)
        entry_1 = tk.Entry(self)

        label_1.grid(row=2, sticky="E")
        entry_1.grid(row=2, column=1)
        browse_1.grid(row=2, column=2)
 

        count = ttk.Button(self, text='Count Fiducials', command=acrelicfunc)
        coord = ttk.Button(self, text='Show Coordinates', command=acrelicfunc)

        count.grid(columnspan=2)
        coord.grid(columnspan=2)
        
        button1 = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(StartPage))
        button1.grid()

        button2 = ttk.Button(self, text="Real Skull", command=lambda: controller.show_frame(realSkull))
        button2.grid()



class acrelicCa(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Phantom!", font=LARGE_FONT)
        label.grid()

        label_1 = tk.Label(self, text='Axial Plane')
        browse_1= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_1 = tk.Entry(self)

        label_2 = tk.Label(self, text='Coronal Plane')
        browse_2= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_2 = tk.Entry(self)

        label_3 = tk.Label(self, text='Sagittal Plane')
        browse_3= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_3 = tk.Entry(self)
        
        label_1.grid(row=2, sticky="E")
        entry_1.grid(row=2, column=1)
        browse_1.grid(row=2, column=2)

        label_2.grid(row=3)
        entry_2.grid(row=3, column=1)
        browse_2.grid(row=3, column=2)

        label_3.grid(row=4)
        entry_3.grid(row=4, column=1)
        browse_3.grid(row=4, column=2)

        count = ttk.Button(self, text='Count Fiducials', command=doNothing)
        coord = ttk.Button(self, text='Show Coordinates', command=doNothing)

        count.grid(columnspan=2)
        coord.grid(columnspan=2)
        
        button1 = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(StartPage))
        button1.grid()

        button2 = ttk.Button(self, text="Real Skull", command=lambda: controller.show_frame(realSkull))
        button2.grid()


class acrelicCb(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Phantom!", font=LARGE_FONT)
        label.grid()

        label_1 = tk.Label(self, text='Axial Plane')
        browse_1= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_1 = tk.Entry(self)

        label_2 = tk.Label(self, text='Coronal Plane')
        browse_2= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_2 = tk.Entry(self)

        label_3 = tk.Label(self, text='Sagittal Plane')
        browse_3= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_3 = tk.Entry(self)
        
        label_1.grid(row=2, sticky="E")
        entry_1.grid(row=2, column=1)
        browse_1.grid(row=2, column=2)

        label_2.grid(row=3)
        entry_2.grid(row=3, column=1)
        browse_2.grid(row=3, column=2)

        label_3.grid(row=4)
        entry_3.grid(row=4, column=1)
        browse_3.grid(row=4, column=2)

        count = ttk.Button(self, text='Count Fiducials', command=doNothing)
        coord = ttk.Button(self, text='Show Coordinates', command=doNothing)

        count.grid(columnspan=2)
        coord.grid(columnspan=2)
        
        button1 = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(StartPage))
        button1.grid()

        button2 = ttk.Button(self, text="Real Skull", command=lambda: controller.show_frame(realSkull))
        button2.grid()

class  glassScan(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Phantom!", font=LARGE_FONT)
        label.grid()

        label_1 = tk.Label(self, text='Axial Plane')
        browse_1= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_1 = tk.Entry(self)

        label_2 = tk.Label(self, text='Coronal Plane')
        browse_2= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_2 = tk.Entry(self)

        label_3 = tk.Label(self, text='Sagittal Plane')
        browse_3= ttk.Button(self, text = "Browse", command = browseFunc, width = 10)
        entry_3 = tk.Entry(self)
        
        label_1.grid(row=2, sticky="E")
        entry_1.grid(row=2, column=1)
        browse_1.grid(row=2, column=2)

        label_2.grid(row=3)
        entry_2.grid(row=3, column=1)
        browse_2.grid(row=3, column=2)

        label_3.grid(row=4)
        entry_3.grid(row=4, column=1)
        browse_3.grid(row=4, column=2)

        count = ttk.Button(self, text='Count Fiducials', command=doNothing)
        coord = ttk.Button(self, text='Show Coordinates', command=doNothing)

        count.grid(columnspan=2)
        coord.grid(columnspan=2)
        
        button1 = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(StartPage))
        button1.grid()

        button2 = ttk.Button(self, text="Real Skull", command=lambda: controller.show_frame(realSkull))
        button2.grid()



app = SeaofBTCapp()
app.mainloop()

