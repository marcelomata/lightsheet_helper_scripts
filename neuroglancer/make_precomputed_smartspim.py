# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 11:26:57 2020

@author: lvbt
"""

import os, numpy as np, igneous.task_creation as tc, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image
from cloudvolume import CloudVolume
from cloudvolume.lib import mkdir, touch
from taskqueue import LocalTaskQueue

def make_info_file(brain, home_dir, volume_size, type_vol = "647", commit=True):
    info = CloudVolume.create_new_info(
    num_channels = 1,
    layer_type = "image", # "image" or "segmentation"
    data_type = "uint16", # 32 not necessary for Princeton atlas, but was for Allen atlas 
    encoding = "raw", # other options: "jpeg", "compressed_segmentation" (req. uint32 or uint64)
    resolution = [ 1810, 1810, 2000 ], # X,Y,Z values in nanometers, 40 microns in each dim. 
    voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
    chunk_size = [ 1024, 1024, 32], # rechunk of image X,Y,Z in voxels, 
    volume_size = volume_size, # X,Y,Z size in voxels
    )
    
    	# If you"re using amazon or the local file system, you can replace "gs" with "s3" or "file"
    vol = CloudVolume("file://"+home_dir+"/"+brain+"/"+type_vol, info=info)
    vol.provenance.description = "TP tracing"
    vol.provenance.owners = ["zmd@princeton.edu"] # list of contact email addresses
    if commit:
        vol.commit_info() # generates gs://bucket/dataset/layer/info json file
        vol.commit_provenance() # generates gs://bucket/dataset/layer/provenance json file
        print("Created CloudVolume info file: ",vol.info_cloudpath)
    return vol
    
def process(args):
    vol,z = args
    img_name = os.path.join(tif_dir, os.path.basename(tif_dir)+"_%06d.tif" % int((z*20)+380))
        
    print("Processing ", img_name)
    assert os.path.exists(img_name) == True
    image = Image.open(img_name)
    width, height = image.size
    
    array = np.array(list( image.getdata() ), dtype=np.uint16, order="F")
    array = array.reshape((1, height, width)).T
    print(array.shape)
    vol[:,:, z] = array
    image.close()
    touch(os.path.join(progress_dir, str(z)))

    return "success"

def make_demo_downsample(type_vol="647", mip_start=0, num_mips=3):
	cloudpath = "file://"+home_dir+"/"+brain+"/"+type_vol
	with LocalTaskQueue(parallel=8) as tq:
		tasks = tc.create_downsampling_tasks(
			cloudpath, 
			mip=mip_start, # Start downsampling from this mip level (writes to next level up)
			fill_missing=False, # Ignore missing chunks and fill them with black
			axis="z", 
			num_mips=num_mips, # number of downsamples to produce. Downloaded shape is chunk_size * 2^num_mip
			chunk_size=[ 128, 128, 32 ], # manually set chunk size of next scales, overrides preserve_chunk_size
			preserve_chunk_size=True, # use existing chunk size, don"t halve to get more downsamples
		  )
		tq.insert_all(tasks)
	print("Done!")

if __name__ == "__main__":
    
    #setting dirs
    home_dir = "/jukebox/LightSheetData/lightserv/jverpeut/natneuroreviews_tompisano_HSV-H129/natneuroreviews_tompisano_HSV-H129_20hr-006/imaging_request_1/viz"
    
    brain = "07142020_tp_hsv20hr_6"
    print(brain)
    
    tif_dir = "/jukebox/LightSheetData/lightserv/jverpeut/natneuroreviews_tompisano_HSV-H129/natneuroreviews_tompisano_HSV-H129_20hr-006/imaging_request_1/output/processing_request_1/resolution_4x/RES(7561x5725x3565)/111940/111940_101428"
    type_vol = "647"
    print(os.path.basename(tif_dir))

    #get x,y,z resolution
    image = Image.open(os.path.join(tif_dir, os.listdir(tif_dir)[0]))
    x, y = image.size
    volume_size = [x, y, len(os.listdir(tif_dir))]
    vol = make_info_file(brain, home_dir, volume_size, type_vol = type_vol)
    
    progress_dir = mkdir(home_dir + "/progress_"+brain+"_"+type_vol)
    done_files = set([ int(z) for z in os.listdir(progress_dir) ])
    all_files = set(range(vol.bounds.minpt.z, vol.bounds.maxpt.z))
    to_upload = [ (vol,int(z)) for z in list(all_files.difference(done_files)) ]
    print("\n # of files to process: %s \n" % len(to_upload))
    to_upload.sort()
    
    print("Running processor...\n")
    with ProcessPoolExecutor(max_workers=10) as executor:
		for job in executor.map(process_slice,to_upload):
			try:
				print(job)
			except Exception as exc:
				print(f'generated an exception: {exc}')
    
    print("Downsampling...\n")
    make_demo_downsample(type_vol, mip_start=0,num_mips=6)
