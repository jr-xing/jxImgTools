# Run tkinter code in another thread
# Source: https://stackoverflow.com/questions/459083/how-do-you-run-your-own-code-alongside-tkinters-event-loop
"""
+------------------------------------------------+
|   +----------------------------------------+   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                 Slice                  |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   |                                        |   |
|   +----------------------------------------+   |
|                                                |
|   +----------------------------------------+   |
|   |                                        |   |
|   |      Stem plot of Dice per slice       |   |
|   |                                        |   |
|   +----------------------------------------+   |
|                                                |
|   +----------------+Slider+----------------+   |
|                                                |
|   Vol Info                                     |
|   +----------------------------------------+   |
|   |                                        |   |
|   +----------------------------------------+   |
|                                                |
|   Slice Info                                   |
|   +----------------------------------------+   |
|   |                                        |   |
|   +----------------------------------------+   |
|                                                |
+------------------------------------------------+

"""
import tkinter as tk
import threading
import numpy as np

from tkinter import StringVar
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

# import mahotas
import numpy.ma as ma

def getDice(seg1, seg2):
    pass

def getDicePerSlice(seg1, seg2):
    pass

from scipy.ndimage.morphology import binary_erosion, generate_binary_structure
def bwperim(BW, dim=3, conn=6):
    # generate_binary_structure and matlab bwperim interpret conn differently
    # Here we keep consist with Matlab function
    # vol = np.bool(vol)    
    BW = BW > 0
    if dim == 2:
        if conn in [4,8]:
            if conn == 4:
                conn = 1
            else:
                conn = 2
    elif dim == 3:
        if conn in [6,18,26]:
            if conn == 6:
                conn = 1
            elif conn == 18:
                conn = 2
            else:
                conn = 3
    # print(dim)
    conn_structure = generate_binary_structure(dim, conn)
    BWErode = binary_erosion(BW, structure=conn_structure)
    BWPeirm = BW ^ BWErode
    return BWPeirm

class VolSlicer(threading.Thread):

    def __init__(self, vol, volInfo = {}, segs = [], slicesInfo = []):
        threading.Thread.__init__(self)
        self.vol = vol
        self.volInfo = volInfo
        self.segs = segs
        self.slicesInfo = slicesInfo
        
        self.sliceIdx = vol.shape[1]//2    
        
        self.start()

    def callback(self):
        self.root.quit()
        
    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        
        # def resize(event):
        #     print(self.root.winfo_width())
        # self.root.bind('<Configure>', resize)
        
        def updateSlice():
            # Show image
            sliceAx.imshow(np.squeeze(self.vol[0,self.sliceIdx-1,:,:,:]), cmap='gray')
            sliceFig.canvas.draw_idle()
            sliceSlider.set(self.sliceIdx)
            
            cmaps = ['autumn', 'winter', 'summer']
            for segIdx, seg in enumerate(self.segs):
                # segSlice = seg[0,self.sliceIdx, :,:,:].squeeze()
                segSlice = bwperim(seg[0,self.sliceIdx, :,:,:].squeeze(), 2, 4)
                
                segSliceMask = ma.masked_array(data = np.ones(segSlice.shape), mask = 1-segSlice)
                # maskedImg = ma.masked_array(data = np.ones(seg.shape), mask = 1-seg)
                # maskedImgSlice = np.squeeze(maskedImg[0,self.sliceIdx-1, :,:,:])
                sliceAx.imshow(segSliceMask, alpha=0.7, cmap = cmaps[segIdx])
            
            # Update slice Info
            sliceInfoStr = ''
            sliceInfoStr += 'Slice {}/{}\n'.format(self.sliceIdx, D)
            for sliceInfoKey in self.slicesInfo[self.sliceIdx-1].keys():
                sliceInfoStr += sliceInfoKey + ':\t' + str(self.slicesInfo[self.sliceIdx-1][sliceInfoKey]) + '\n'
            sliceInfoLabel['text'] = sliceInfoStr
        
        def onLeftArrowKey(event):
            self.sliceIdx = max(1, self.sliceIdx - 1)
            updateSlice()
        def onRightArrowKey(event):
            self.sliceIdx = min(D, self.sliceIdx + 1)
            updateSlice()
        
        
        self.root.bind('<Left>', onLeftArrowKey)
        self.root.bind('<Right>', onRightArrowKey)
        
        [N, D, H, W, C] = self.vol.shape
        sliceFig = Figure(figsize=(5, 4), dpi=100)        
        sliceAx = sliceFig.add_subplot(111)
        sliceAx.imshow(np.squeeze(self.vol[0,self.sliceIdx, :,:,:]), cmap='gray')

        sliceCanvas = FigureCanvasTkAgg(sliceFig, master=self.root)  # A tk.DrawingArea.
        sliceCanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        sliceCanvas.draw()
        
        
        toolbar = NavigationToolbar2Tk(sliceCanvas, self.root)
        toolbar.update()
              
        def on_key_press(event):
            print("you pressed {}".format(event.key))
            key_press_handler(event, sliceCanvas, toolbar)
        sliceCanvas.mpl_connect("key_press_event", on_key_press)
        
        
        # def _quit():
        #     root.quit()     # stops mainloop
        #     root.destroy()  # this is necessary on Windows to prevent
        #                     # Fatal Python Error: PyEval_RestoreThread: NULL tstate
        
        def sliceSliderChange(event):            
            self.sliceIdx = int(event)
            updateSlice()
            
        # button = tk.Button(master=self.root, text="Quit", command=pp)
        # button.pack(side=tk.BOTTOM)
        
        # Plot Dice per slice if provided
        dicePerSlice = self.volInfo.get('DicePerSlice', None)
        if dicePerSlice is not None:            
            dicePlotFig = Figure(figsize = (1,1))
            dicePlotAx = dicePlotFig.add_subplot(111)
            dicePlotAx.stem(dicePerSlice, use_line_collection = True)
            dicePlotAx.set_xlabel('SliceIdx')
            dicePlotAx.set_ylabel('Dice')
            dicePlotCanvas = FigureCanvasTkAgg(dicePlotFig, master=self.root)
            dicePlotCanvas.get_tk_widget().pack(side=tk.TOP, fill='x', expand=0)
            dicePlotCanvas.draw()
            
        # Choose slice to show
        sliceSlider = tk.Scale(master = self.root, from_= 1, to_=D, orient=tk.HORIZONTAL, command=sliceSliderChange, length=350)
        sliceSlider.set(self.sliceIdx)
        sliceSlider.place(relwidth=1)
        sliceSlider.pack(side = tk.TOP, expand = False)
        
        # Show information of current slice
        sliceInfoHeaderLabel = tk.Label(self.root, text='Slice Info')
        sliceInfoHeaderLabel.pack(side=tk.TOP)        
                
        sliceInfoLabel = tk.Label(self.root, text = '')
        sliceInfoLabel.pack(side=tk.TOP)
        
        # Show information of whole volume
        volInfoHeaderLabel = tk.Label(self.root, text='Volume Info')
        volInfoHeaderLabel.pack(side=tk.TOP)
        
        volInfoStr = ''
        for volInfoKey in self.volInfo.keys():
            if volInfoKey.lower() != 'diceperslice':
                volInfoStr += volInfoKey + '\t' + str(self.volInfo[volInfoKey]) + '\n'
        volInfoLabel = tk.Label(self.root, text=volInfoStr)
        volInfoLabel.pack(side=tk.TOP)
        
        

        self.root.mainloop()

import SimpleITK as sitk
def safeLoadMedicalImg(filename):
    """Load single image file of common medical image types
    

    Parameters
    ----------
    filename : TYPE
        DESCRIPTION.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    img : TYPE
        DESCRIPTION.

    """
    
    img = sitk.GetArrayFromImage(sitk.ReadImage(filename))
    if np.ndim(img) != 3:
        raise ValueError(f'Unsupported image dim {np.ndim(img)} (with shape {img.shape})')
    
    # Strangely, [80, 70, 50] image become [50, 80, 70]!
    # i.e. [H, W, N] => [N, H, W]
    img = np.moveaxis(img, 0, 2)
    
    #sliceDim = 2 if sliceDim == -1 else sliceDim
    #img = np.moveaxis(img, sliceDim, -1)
    return img
# img = np.random.rand(128,128)
# vol = np.random.rand(1, 50, 128, 128, 1)
if __name__ == '__main__':
    volRaw = safeLoadMedicalImg('./ep2d_dbsi_22_3X3mm_4d_001-axi-odd.nii')
    segRaw = safeLoadMedicalImg('./ep2d_dbsi_22_3X3mm_4d_001.labels-axi-odd.nii')
    seg4Raw = safeLoadMedicalImg('./ep2d_dbsi_22_3X3mm_4d_004.labels-axi-odd.nii')
    vol = np.moveaxis(volRaw, -1,0)[np.newaxis, :,:,:,np.newaxis]
    seg = np.moveaxis(segRaw, -1,0)[np.newaxis, :,:,:,np.newaxis]
    seg4 = np.moveaxis(seg4Raw, -1,0)[np.newaxis, :,:,:,np.newaxis]
    # seg = mahotas.bwperim(seg, 16)
    volInfo = {
        'DicePerSlice': np.random.rand(50),
        'Seg Method': 'Graph Cut'
        }
    slicesInfo = [{'Dice': 0.5}]*50
    app = VolSlicer(vol, volInfo = volInfo, slicesInfo = slicesInfo, segs=[seg, seg4])
# print('Now we can continue running code while mainloop runs!')

# for i in range(20):
#     print(i)