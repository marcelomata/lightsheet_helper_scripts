# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 14:59:21 2020

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
    resolution = [ 1866, 1866, 4000 ], # X,Y,Z values in nanometers, 40 microns in each dim. 
    voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
    chunk_size = [ 1024, 1024, 1], # rechunk of image X,Y,Z in voxels, 
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
    img_name = os.path.join(tif_dir, "090560_107801_%06d.tif" % int((z*40)+240)) #ZMD CHANGED FOR CUSTOM DSET
        
    print("Processing ", img_name)
    assert os.path.exists(img_name) == True
    image = Image.open(img_name)
    width, height = image.size
    
    array = np.array(list( image.getdata() ), dtype=np.uint16, order="F")
    array = array.reshape((1, height, width)).T
    print(array.shape)
    vol[:,:, z] = array
    print("\nExported to Cloudvolume!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    image.close()
    touch(os.path.join(progress_dir, str(z)))

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
    home_dir = "/jukebox/scratch/zmd/save/contra_ipsi_projection_studies_20191125"
    
    brain = str(sys.argv[1])
    print(brain)
    
    tif_dir = "/jukebox/LightSheetTransfer/tp/20200701_14_15_35_20180205_jg_b6f_04/Ex_642_Em_2/stitched/RES(7552x5666x1628)/090560/090560_107801"
    type_vol = "647"

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
    with ProcessPoolExecutor(max_workers=12) as executor:
        executor.map(process, to_upload)
    
    print("Downsampling...\n")
    make_demo_downsample(type_vol, mip_start=0,num_mips=7)