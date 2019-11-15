#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 14:44:30 2019

@author: wanglab
"""

#######################################
#%%Example eroding only edges
ann_path = '/jukebox/LightSheetTransfer/atlas/allen_atlas/annotation_template_25_sagittal_forDVscans.tif'
new_erode_path = '/home/wanglab/LightSheetTransfer/atlas/allen_atlas/annotation_template_25_sagittal_forDVscans_75um_erosion.tif'
zyx_scale = (25,25,25)
microns_to_erode = 75


#NOTE THIS ESSENTIALLY SCALES PIXEL SPACE*****
from scipy.ndimage.morphology import distance_transform_edt
import numpy as np
from skimage.external import tifffile
ann = tifffile.imread(ann_path)
distance_space_inside = distance_transform_edt(ann.astype('bool'), sampling=zyx_scale)*-1 #INSIDE
distance_space_inside = np.abs(distance_space_inside)
mask = np.copy(distance_space_inside)
mask[distance_space_inside<=microns_to_erode] = 0

#zero out edges
eann = np.copy(ann)
eann[mask==0]=0
tifffile.imsave(new_erode_path, eann)

#######################################
#%%Example eroding edges and ventricles
ann_path = '/home/wanglab/mounts/LightSheetTransfer/atlas/annotation_sagittal_atlas_20um_iso.tif'
new_erode_path = '/home/wanglab/mounts/wang/zahra/prv/pma_annotation_sagittal_atlas_20um_iso_60um_edge_160um_vntric_erosion.tif'
#get ventricles - these are the values of ventricles in the annotation image (also the same as the look up file)
ventricle_values = [108.0, 81.0, 116.0, 129.0, 145.0, 73.0]
ventricular_microns_to_erode = 80
edge_microns_to_erode = 60
zyx_scale = (20,20,20)

#NOTE THIS ESSENTIALLY SCALES PIXEL SPACE*****
import numpy as np
from skimage.external import tifffile
import SimpleITK as sitk
ann = sitk.GetArrayFromImage(sitk.ReadImage((ann_path)))
from scipy.ndimage.morphology import distance_transform_edt
distance_space_inside = distance_transform_edt(ann.astype('bool'), sampling=zyx_scale)*-1 #INSIDE
distance_space_inside = np.abs(distance_space_inside)

#zero out edges
mask = np.copy(distance_space_inside)
mask[distance_space_inside<=edge_microns_to_erode] = 0
eann = np.copy(ann)
eann[mask==0]=0
ann = np.copy(eann)

#now ventricles
vann = np.copy(ann)
vann[vann==0.0] = 1 
vmask = np.isin(vann, ventricle_values)
vann[vmask] = 0.0 #erode out nonventricular space adjacent to ventricles
vann[vann!=0.0] = 1 
distance_space_inside = distance_transform_edt(vann.astype('bool'), sampling=zyx_scale)*-1 #INSIDE
distance_space_inside = np.abs(distance_space_inside)
mask = np.copy(distance_space_inside)
mask[distance_space_inside<=ventricular_microns_to_erode] = 0

#zero out ventricles
eann = np.copy(ann)
eann[mask==0]=0

#now set anything that has been eroded to 73.0==ventricular systems
voxs = np.where(eann != ann)
eann[voxs] = 73.0
tifffile.imsave(new_erode_path, eann)
