#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 11:09:29 2018

@author: wanglab
"""

import numpy as np, os, time, cv2
from skimage.external import tifffile
import matplotlib.pyplot as plt
import pandas as pd

def resize_merged_stack(pth, dst, dtype = "uint16", resizef = 3):
    """
    resize function for large image stacks using cv2
    inputs:
        pth = 4d stack, memmap array or numpy array
        dst = path of tif file to save
        dtype = default uint16
        resizef = default 6
    """

    #read file
    if pth[-4:] == ".tif": img = tifffile.imread(pth)
    elif pth[-4:] == ".npy": img = np.lib.format.open_memmap(pth, dtype = dtype, mode = "r")
    else: img = pth #if array was input

    z,y,x,ch = img.shape
    resz_img = np.zeros((z, int(y/resizef), int(x/resizef), ch))

    for i in range(z):
        for j in range(ch):
            #make the factors - have to resize both image and cell center array
            xr = int(img[i, :, :, j].shape[1] / resizef); yr =  int(img[i, :, :, j].shape[0] / resizef)
            im = cv2.resize(img[i, :, :, j], (xr, yr), interpolation=cv2.INTER_LINEAR)
            resz_img[i, :, :, j] = im.astype(dtype)

    tifffile.imsave(dst, resz_img.astype(dtype))

    return dst

def check_cell_center_to_fullsizedata(brain, zstart, zstop, dst, resizef):
    """
    maps cnn cell center coordinates to full size cell channel images
    inputs:
        brain = path to lightsheet processed directory
        zstart = beginning of zslice
        zstop = end of zslice
        dst = path of tif stack to save
    NOTE: 20+ PLANES CAN OVERLOAD MEMORY
    """
    start = time.time()

    #doing things without loading parameter dict
    data = os.listdir(os.path.join(brain, "full_sizedatafld")); data.sort()

    #exception if only 1 channel is imaged
    if len(data) == 1:
        cellch = os.path.join(brain, "full_sizedatafld/"+data[0])
    elif len(data) < 3 and len(data) > 1:
        cellch = os.path.join(brain, "full_sizedatafld/"+data[1])
    else:
        cellch = os.path.join(brain, "full_sizedatafld/"+data[2])

    #not the greatest way to do things, but works
    src = [os.path.join(cellch, xx) for xx in os.listdir(cellch) if xx[-3:] == "tif" and int(xx[-7:-4]) in range(zstart, zstop)]; src.sort()

    raw = np.zeros((len(src), tifffile.imread(src[0]).shape[0], tifffile.imread(src[0]).shape[1]))

    for i in range(len(src)):
        raw[i, :, :] = tifffile.imread(src[i])

    pth = os.path.join(brain, "3dunet_output/pooled_cell_measures/"+os.path.basename(brain)+"_cell_measures.csv")
    cells = pd.read_csv(pth)

    cells = cells[(cells["z"] >= zstart) & (cells["z"] <= zstop-1)] #-1 to account for range

    cell_centers = np.zeros(raw.shape)

    for i, r in cells.iterrows():
        cell_centers[r["z"]-zstart, r["y"]-5:r["y"]+5, r["x"]-5:r["x"]+5] = 50000

    rbg = np.stack([raw.astype("uint16"), cell_centers.astype("uint16"), np.zeros_like(raw)], -1)

    resize_merged_stack(rbg, os.path.join(dst, "{}_raw_cell_centers_resized_z{}-{}.tif".format(os.path.basename(brain),
                                          zstart, zstop)), "uint16", resizef)

    print("took %0.1f seconds to make merged maps for %s" % ((time.time()-start), brain))

def check_cell_center_to_resampled(brain, zstart, zstop, dst):
    """
    maps cnn cell center coordinates to resampled stack
    inputs:
        brain = path to lightsheet processed directory
        zstart = beginning of zslice
        zstop = end of zslice
        dst = path of tif stack to save
    NOTE: 20+ PLANES CAN OVERLOAD MEMORY
    """
    start = time.time()

    #doing things without loading parameter dict, could become a problem
    tifs = [xx for xx in os.listdir(brain) if xx[-4:] == ".tif"]; tifs.sort()
    raw = tifffile.imread(tifs[len(tifs)-1])

    pth = os.path.join(brain, "3dunet_output/pooled_cell_measures/"+os.path.basename(brain)+"_cell_measures.csv")
    cells = pd.read_csv(pth)

    cells = cells[(cells["z"] >= zstart) & (cells["z"] <= zstop-1)] #-1 to account for range

    cell_centers = np.zeros(raw.shape)

    for i, r in cells.iterrows():
        cell_centers[r["z"]-zstart-5:r["z"]-zstart+5, r["y"]-10:r["y"]+5, r["x"]-5:r["x"]+5] = 50000

    rbg = np.stack([raw.astype("uint16"), cell_centers.astype("uint16"), np.zeros_like(raw)], -1)

    resize_merged_stack(rbg, os.path.join(dst, "{}_raw_cell_centers_resized_z{}-{}.tif".format(os.path.basename(brain),
                                          zstart, zstop)), "uint16", 6)

    print("took %0.1f seconds to make merged maps for %s" % ((time.time()-start), brain))


if __name__ == "__main__":

    ids = ["z265"]

    for i in ids:
        brain = "/jukebox/LightSheetData/rat-brody/processed/201910_tracing/"+i
        zstart = 200; zstop = 205
        dst = "/jukebox/LightSheetData/rat-brody/processed/201910_tracing/validation"
        if not os.path.exists(dst): os.mkdir(dst)

        check_cell_center_to_fullsizedata(brain, zstart, zstop, dst, 1)
