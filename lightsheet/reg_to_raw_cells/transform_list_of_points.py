#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 18:47:47 2018

@author: tpisano

Set of functions to take a list of points and transform them into new space

# NEED ELASTIX TO RUN THIS (so run on a LINUX machine)

"""

import os, sys, numpy as np, shutil
from scipy.io import loadmat
import pickle

def transform_points(src, dst, transformfiles, resample_points=False, param_dictionary_for_reorientation=False):
	"""
	
	Inputs
	---------
	src = numpy file consiting of nx3 (ZYX points)
	dst = folder location to write points
	transformfiles = 
		list of all elastix transform files used, and in order of the original transform****
	resample_points = [original_dims, resample_dims] if there was resampling done, use this here
	param_dictionary_for_reorientation = param_dictionary for lightsheet package to use for reorientation
	"""
	#load
	src = np.load(src) # x,y,z, sagittal == z,y,x horizontal 
	src[:,[0,2]] = src[:,[2,0]] # z,y,x, sagittal
	
	print("generating pretransform_text_file")
	#generate text file
	pretransform_text_file = create_text_file_for_elastix(src, dst)
	print("copying over elastix files")
	#copy over elastix files 
	# transformfiles = modify_transform_files(transformfiles, dst)
	print("running transformix on points")
	#run transformix on points
	points_file = point_transformix(pretransform_text_file, transformfiles[-1], dst)
	print("converting points into structure counts")
	#convert registered points into structure counts
	npy_file = unpack_pnts(points_file, dst)   
	
	# #optionally resample points
	# if resample_points:
	#     original_dims, resample_dims = resample_points
	#     src = points_resample(src, original_dims, resample_dims)

	return npy_file
	
def makedir(dst):
	if not os.path.exists(dst):os.mkdir(dst)
	return
	
def create_text_file_for_elastix(src, dst):
	"""
	
	Inputs
	---------
	src = numpy file consiting of nx3 (ZYX points)
	dst = folder location to write points
	"""
	
	print("This function assumes ZYX centers...")
	
	#setup folder
	makedir(dst)
								 
	#create txt file, with elastix header, then populate points
	pth=os.path.join(dst, "zyx_points_pretransform.txt")
	
	#load
	if type(src) == np.ndarray:
		arr = src
	else:
		arr = np.load(src) if src[-3:] == "npy" else loadmat(src)["cell_centers_orig_coord"]
	
	#convert
	stringtowrite = "\n".join(["\n".join(["{} {} {}".format(i[2], i[1], i[0])]) for i in arr]) ####this step converts from zyx to xyz*****
	
	#write file
	sys.stdout.write("writing centers to transfomix input points text file..."); sys.stdout.flush()
	with open(pth, "w+") as fl:
		fl.write("index\n{}\n".format(len(arr)))    
		fl.write(stringtowrite)
		fl.close()
	sys.stdout.write("...done writing centers\n"); sys.stdout.flush()
		
	return pth

def modify_transform_files(transformfiles, dst):
	"""Function to copy over transform files, modify paths in case registration was done on the cluster, and tether them together
	
		Inputs
	---------
	transformfiles = 
		list of all elastix transform files used, and in order of the original transform****
	
	"""
	
	#new
	ntransformfiles = [os.path.join(dst, "order{}_{}".format(i,os.path.basename(xx))) for i,xx in enumerate(transformfiles)]
	
	#copy files over
	[shutil.copy(xx, ntransformfiles[i]) for i,xx in enumerate(transformfiles)]
	
	#modify each with the path
	for i,pth in enumerate(ntransformfiles):
		
		#skip first
		if i!=0:
			
			#read
			with open(pth, "r") as fl:
				lines = fl.readlines()
				fl.close()
			
			#copy
			nlines = lines
			
			#iterate
			for ii, line in enumerate(lines):
				if "(InitialTransformParametersFileName" in line:
					nlines[ii] = "(InitialTransformParametersFileName {})\n".format(ntransformfiles[i-1])
			
			#write
			with open(pth, "w") as fl:
				for nline in lines:
					fl.write(str(nline))
				fl.close()
		
	return ntransformfiles
   
def point_transformix(pretransform_text_file, transformfile, dst):
	"""apply elastix transform to points
	
	
	Inputs
	-------------
	pretransform_text_file = list of points that already have resizing transform
	transformfile = elastix transform file
	dst = folder
	
	Returns
	---------------
	trnsfrm_out_file = pth to file containing post transformix points
	
	"""
	sys.stdout.write("\n***********Starting Transformix***********")
	from subprocess import check_output
	#set paths    
	trnsfrm_out_file = os.path.join(dst, "outputpoints.txt")
	
	#run transformix point transform
	call = "transformix -def {} -out {} -tp {}".format(pretransform_text_file, dst, transformfile)
	print(check_output(call, shell=True))
	sys.stdout.write("\n   Transformix File Generated: {}".format(trnsfrm_out_file)); sys.stdout.flush()
	return trnsfrm_out_file


def unpack_pnts(points_file, dst):
	"""
	function to take elastix point transform file and return anatomical locations of those points
	
	Here elastix uses the xyz convention rather than the zyx numpy convention
	
	Inputs
	-----------
	points_file = post_transformed file, XYZ
	
	Returns
	-----------
	dst_fl = path to numpy array, ZYX
	
	"""   

	#####inputs 
	assert type(points_file)==str
	point_or_index = 'OutputPoint'
	
	#get points
	with open(points_file, "r") as f:                
		lines=f.readlines()
		f.close()

	#####populate post-transformed array of contour centers
	sys.stdout.write("\n\n{} points detected\n\n".format(len(lines)))
	arr=np.empty((len(lines), 3))    
	for i in range(len(lines)):        
		arr[i,...]=lines[i].split()[lines[i].split().index(point_or_index)+3:lines[i].split().index(point_or_index)+6] #x,y,z
			
	#optional save out of points
	dst_fl = os.path.join(dst, "posttransformed_zyx_voxels.npy")
	np.save(dst_fl, np.asarray([(z,y,x) for x,y,z in arr]))
	
	#check to see if any points where found
	print("output array shape {}".format(arr.shape))
		
	return dst_fl

def points_resample(src, original_dims, resample_dims, verbose = False):
	"""Function to adjust points given resizing by generating a transform matrix
	
	***Assumes ZYX and that any orientation changes have already been done.***
	
	src: numpy array or list of np arrays of dims nx3
	original_dims (tuple)
	resample_dims (tuple)
	"""
	src = np.asarray(src)
	assert src.shape[-1] == 3, "src must be a nx3 array"
	
	#initialize
	d1,d2=src.shape
	nx4centers=np.ones((d1,d2+1))
	nx4centers[:,:-1]=src
	
	#acount for resampling by creating transformmatrix
	zr, yr, xr = resample_dims
	z, y, x = original_dims
	
	#apply scale diff
	trnsfrmmatrix=np.identity(4)*(zr/float(z), yr/float(y), xr/float(x), 1)
	if verbose: sys.stdout.write("trnsfrmmatrix:\n{}\n".format(trnsfrmmatrix))
	
	#nx4 * 4x4 to give transform
	trnsfmdpnts=nx4centers.dot(trnsfrmmatrix) ##z,y,x
	if verbose: sys.stdout.write("first three transformed pnts:\n{}\n".format(trnsfmdpnts[0:3]))

	return trnsfmdpnts


def load_dictionary(pth):
	"""simple function to load dictionary given a pth
	"""
	kwargs = {};
	with open(pth, "rb") as pckl:
		kwargs.update(pickle.load(pckl))
		pckl.close()

	return kwargs

#%%
if __name__ == "__main__":
	
	###NOTE CHECK TO ENSURE ACCOUNTING FOR INPUT RESAMPLING, and ORIENTATION CHANGE*****
	
	# from tools.registration.transform_list_of_points import *
	from tools.registration.register import change_interpolation_order
	# from tools.registration.transform_list_of_points import modify_transform_files
	#inputs
	#numpy file consiting of nx3 (ZYX points) or if .mat file structure where zyx is called "cell_centers_orig_coord"
	# src = "/home/wanglab/Downloads/transform_test/nx3_zyx_points.npy"
	# dst = "/home/wanglab/Downloads/transform_test"; makedir(dst) # folder location to write points
	# brain = "/home/ahoag/ngdemo/data/test_raw_cells/an21/"
	brain = "/jukebox/wang/Jess/lightsheet_output/201904_ymaze_cfos/processed/an22"

	src = "/jukebox/wang/Jess/lightsheet_output/201904_ymaze_cfos/processed/an22/clearmap_cluster_output/cells_transformed_to_Atlas.npy" # x,y,z sagittal 
	dst = "/home/wanglab/Desktop/cell_erosion_test"

	# np.save(src, (np.random.rand(10,3)*20).astype("int"))
	 
	#EXAMPLE USING CLEARMAP - when marking centers in the  "raw" full sized cfos channel. This will transform those centers into "atlas" space (in this case the moving image)
	#list of all elastix transform files used, and in order of the original transform****
	a2r0 = os.path.join(brain, "clearmap_cluster_output/elastix_cfos_to_auto/TransformParameters.0.txt")
	a2r1 = os.path.join(brain, "clearmap_cluster_output/elastix_cfos_to_auto/TransformParameters.1.txt")
	r2s0 = os.path.join(brain, "clearmap_cluster_output/elastix_auto_to_atlas/TransformParameters.0.txt")
	r2s1 = os.path.join(brain, "clearmap_cluster_output/elastix_auto_to_atlas/TransformParameters.1.txt")

	#set destination directory
	braindst = dst 

	# makedir(braindst)
	# print("made brain directory: ",braindst)    
	# aldst = os.path.join(braindst, "transformed_annotations"); makedir(aldst)
	#
	## transformix
	# first copy over files to new location
	transformfiles = modify_transform_files(transformfiles=[a2r0, a2r1, r2s0, r2s1], dst = braindst)
	# change order of interpolation in new copied files
	[change_interpolation_order(xx,0) for xx in transformfiles]
	print("running transformation")
	#apply - resample_points not accounted for yet in cfos
	npy_file = transform_points(src, dst, transformfiles) # z,y,x, sagittal
	# Now figure out the factor I need to multiply each coordinate by to get it into raw space.
	# This factor is N_x_raw/N_x_downsampledforelastix, 
	# N_x_raw can be found from loading in one file from the raw volumes for this brain
	# N_x_downsampledforelastix can be found from loading in the cfos_resampled.tif file 
	# in the clearmap_cluster_output/ directory of a brain directory
	x_dim_raw_h = 2160
	y_dim_raw_h = 2560
	z_dim_raw_h = 687

	# from cfos_resample.tif file which is in z,y,x
	x_dim_resampled_s = 429
	y_dim_resampled_s = 800
	z_dim_resampled_s = 675

	x_dim_resampled_h = z_dim_resampled_s
	y_dim_resampled_h = y_dim_resampled_s
	z_dim_resampled_h = x_dim_resampled_s

	coordinates = np.load(npy_file) # z,y,x, sagittal == x,y,z horizontal
	coordinates[:,[0,2]] = coordinates[:,[2,0]] # z,y,x, horizontal

	x_factor_h = x_dim_raw_h/float(x_dim_resampled_h)
	y_factor_h = y_dim_raw_h/float(y_dim_resampled_h)
	z_factor_h = z_dim_raw_h/float(z_dim_resampled_h)

	# print(coordinates)
	coordinates *= np.array([z_factor_h,y_factor_h,y_factor_h]) # still, z,y,x horizontal
	final_coordinates_filename = npy_file.replace('.npy','_raw.npy')
	np.save(final_coordinates_filename,coordinates.astype(int))
	print(f"saved {final_coordinates_filename}")

#%%
    #check if mapping is correct, don't need to run if you are confident the script works
    import matplotlib.pyplot as plt
    cells = coordinates.astype(int)
    #map all cells to vol
    cellvol = np.zeros((z_dim_raw_h,y_dim_raw_h,x_dim_raw_h))
    # cellrs = cells.T[:3].T.astype(int)
    for i,cell in enumerate(cells):
        #only map if non negative coordinates
        if i%100000==0: print("%s cells mapped" % i)
        try:
            cellvol[cell[0],cell[1],cell[2]] = 255
        except:
            print("Cell coordinate out of bounds")
            
    plt.imshow(np.max(cellvol[500:600],axis=0))
