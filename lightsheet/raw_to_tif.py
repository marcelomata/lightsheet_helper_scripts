#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 17:24:59 2020

@author: wanglab
"""

import tifffile as tif, numpy as np, os, multiprocessing as mp

def convert(pth):
    fd = open(pth, 'rb')
    rows = 1600
    cols = 2000
    f = np.fromfile(fd, dtype=np.uint16,count=rows*cols)
    im = f.reshape((rows, cols)) #notice row, column format
    fd.close()
    tif.imsave(pth[:-3]+"tif",im.astype("uint16"))
    
    print("\n"+pth[:-3]+"tif")
    return
        
src = "/jukebox/LightSheetTransfer/tp/20200813_14_35_22_20170419_db_bl6_cri_rpv_53h_ventral_up/Ex_642_Em_2"
for fld in os.listdir(src):
    print(fld)
    fld = os.path.join(src, fld)
    for imgfld in os.listdir(fld):
        print(imgfld)
        pth = os.path.join(fld, imgfld)
        pths = [os.path.join(pth, xx) for xx in os.listdir(pth) if "raw" in xx and not os.path.exists(os.path.join(pth, xx[:-3]+"tif"))]
        if len(pths)>0:
            with mp.Pool(processes=12) as pool:
                pool.map(convert,pths)

