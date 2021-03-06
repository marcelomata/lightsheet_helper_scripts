#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 10:21:32 2019

@author: wanglab
"""

import pandas as pd, matplotlib.pyplot as plt, seaborn as sns, os
from skimage.external import tifffile
import SimpleITK as sitk, numpy as np, scipy
os.chdir("/jukebox/wang/zahra/lightsheet_copy")
from tools.registration.allen_structure_json_to_pandas import annotation_location_to_structure
from tools.analysis.network_analysis import make_structure_objects
from tools.utils.io import listdirfull, makedir
os.chdir("/jukebox/wang/zahra/clearmap_cluster_copy")
from ClearMap.Analysis.Voxelization import voxelize
import ClearMap.Analysis.Statistics as stat
import ClearMap.Alignment.Resampling as rsp
import ClearMap.IO.IO as io

tab20cmap = [plt.cm.tab20(xx) for xx in range(20)]
tab20cmap_nogray = tab20cmap[:14] + tab20cmap[16:]
import matplotlib
tab20cmap_nogray = matplotlib.colors.ListedColormap(tab20cmap_nogray, name = "tab20cmap_nogray")
import matplotlib.patches as mpatches
sns.set_style("white")

def make_heatmaps(pth, subdir):
    """ makes clearmap style heatmaps """
    
    #make heatmaps
    vox_params = {"method": "Spherical", "size": (15, 15, 15), "weights": None}
    
    if subdir in os.listdir(pth):
        points = np.load(os.path.join(pth, subdir+"/posttransformed_zyx_voxels.npy"))
        
        #run clearmap style blurring
        vox = voxelize(np.asarray(points), dataSize = (456, 528, 320), **vox_params)
        dst = os.path.join(pth, subdir+"/cells_heatmap.tif")
        tifffile.imsave(dst, vox.astype("int32"))
    else:
        print("no transformed cells")
    return dst

def consolidate_parents_structures_cfos(id_table, ann, namelist, verbose=False, structures=False):
    """Function that generates evenly spaced pixels values based on annotation parents

    Removes 0 from list

    Inputs:
        id_table=path to excel file generated from scripts above
        ann = allen annoation file
        namelist=list of structues names, typically parent structures*********************

    Returns:
        -----------
        nann = new array of bitdepth
        list of value+name combinations
    """
    if type(ann) == str: ann = sitk.GetArrayFromImage(sitk.ReadImage(ann))


    #remove duplicates and null and root
    namelist = list(set(namelist))
    namelist = [xx for xx in namelist if xx != "null" and xx != "root"]
    namelist.sort()

    #make structures to find parents
    if not structures:
        from tools.analysis.network_analysis import make_structure_objects
        structures = make_structure_objects(id_table)

    #setup
    nann = np.zeros(ann.shape).astype("uint8")
    cmap = [xx for xx in np.linspace(1,255, num=len(namelist))]

    #populate
    for i in range(len(namelist)):
        try:
            nm=namelist[i]
            s = [xx for xx in structures if xx.name==nm][0]
            if verbose: print ("{}, {} of {}, value {}".format(nm, i, len(namelist)-1, cmap[i]))
            nann[np.where(ann==int(s.idnum))] = cmap[i]
            for ii in s.progeny:
                if ii[3] != "null": nann[np.where(ann==int(ii[3]))] = cmap[i]
        except Exception,e:
            print nm, e
    #sitk.Show(sitk.GetImageFromArray(nann))
    #change nann to have NAN where zeros
    nann = nann.astype("float")
    nann[nann == 0] = "nan"

    return nann, zip(cmap[:], namelist)

def make_2D_overlay_of_heatmaps(src, atl_pth, ann_pth, allen_id_table, save_dst, positive = True, negative = True):
    
    vol = tifffile.imread(src)
    atl = tifffile.imread(atl_pth)
    ann = tifffile.imread(ann_pth)
    
    pvol = vol[:,:,:,1]
    nvol = vol[:,:,:,0]
    atl = np.rot90(np.transpose(atl, [1, 0, 2]), axes = (2,1)) #sagittal to coronal
    ann = np.rot90(np.transpose(ann, [1, 0, 2]), axes = (2,1)) #sagittal to coronal
    
    assert atl.shape == ann.shape == nvol.shape
    
    pix_values = list(np.unique(ann.ravel().astype("int64")))
    
    #collect names of parents OR ##optionally get sublist
    #make structures to find parents
    structures = make_structure_objects(allen_id_table)
    parent_list = list(set([yy.parent[1] for xx in pix_values for yy in structures if xx == yy.idnum]))
    
    #find counts of highest labeled areas
    olist = annotation_location_to_structure(allen_id_table, args=zip(*np.nonzero(pvol[100:175])), ann=ann[100:175])
    srt = sorted(olist, key=lambda x: x[0], reverse=True)
    parent_list = [xx[1] for xx in srt]
    
    #generate list of structures present
    #nann, lst = consolidate_parents_structures(allen_id_table, ann, parent_list, verbose=True)
    
    #threshold values
    pvol[pvol!=0.0] = 1.0
    nvol[nvol!=0.0] = 1.0
    no_structures_to_keep = 20
    
    #loop only positives
    zstep = 40
    colorbar_cutoff = 65#20,60 #this is related to zstep size...(it"s like  apercetnage...)
    rngs = range(0, 558, zstep)
    for iii in range(len(rngs)-1):
        #range rng = (100,150)
        rng = (rngs[iii], rngs[iii+1])
    
        #positive
        if positive:
            print(rng, "positive")
            #get highest
            olist = annotation_location_to_structure(allen_id_table, zip(*np.nonzero(pvol[rng[0]:rng[1]])), ann[rng[0]:rng[1]])
            srt = sorted(olist, key=lambda x: x[0], reverse=True)
            parent_list = [xx[1] for xx in srt]
            #select only subset
            parent_list=parent_list[:no_structures_to_keep]
            nann, lst = consolidate_parents_structures_cfos(allen_id_table, ann[rng[0]:rng[1]], parent_list, verbose=True, structures=structures)
    
            #make fig
            plt.figure(figsize=(15,18))
            ax = plt.subplot(2,1,1)
            fig = plt.imshow(np.max(atl[rng[0]:rng[1]], axis=0), cmap="gray", alpha=1)
            fig.axes.get_xaxis().set_visible(False)
            fig.axes.get_yaxis().set_visible(False)
            ax.set_title("ABA structures")
            mode = scipy.stats.mode(nann, axis=0, nan_policy="omit") #### THIS IS REALLY IMPORTANT
            most = list(np.unique(mode[1][0].ravel())); most = sorted(most, reverse=True)
            ann_mode = mode[0][0]
            masked_data = np.ma.masked_where(ann_mode < 0.1, ann_mode)
            im = plt.imshow(masked_data, cmap=tab20cmap_nogray, alpha=0.8, vmin=0, vmax=255)
            patches = [mpatches.Patch(color=im.cmap(im.norm(i[0])), label="{}".format(i[1])) for i in lst]
            plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )
            ax.set_anchor("W")
    
            #pvals
            ax = plt.subplot(2,1,2)
            ax.set_title("Number of positively correlated voxels in AP dimension")
            #modify colormap
            import matplotlib as mpl
            my_cmap = plt.cm.viridis(np.arange(plt.cm.RdBu.N))
            #my_cmap = plt.cm.RdYlGn(np.arange(plt.cm.RdBu.N))
            my_cmap[:colorbar_cutoff,:4] = 0.0
            my_cmap = mpl.colors.ListedColormap(my_cmap)
            my_cmap.set_under("w")
            #plot
            fig = plt.imshow(np.max(atl[rng[0]:rng[1]], axis=0), cmap="gray", alpha=1)
            #plt.imshow(np.max(pvol[rng[0]:rng[1]], axis=0), cmap=my_cmap, alpha=0.9) #old way
            plt.imshow(np.sum(pvol[rng[0]:rng[1]], axis=0), cmap=my_cmap, alpha=0.95, vmin=0, vmax=zstep)
            plt.colorbar()
            fig.axes.get_xaxis().set_visible(False)
            fig.axes.get_yaxis().set_visible(False)
            ax.set_anchor("W")
            #plt.tight_layout()
            pdst = os.path.join(save_dst, "positive_overlays_zstep{}".format(zstep))
            if not os.path.exists(pdst): os.mkdir(pdst)
            plt.savefig(os.path.join(pdst, "cfos_z{}-{}.pdf".format(rng[0],rng[1])), dpi=300, transparent=True)
            plt.close()
    
        #negative
        if negative:
            print rng, "negative"
            #get highest
            olist = annotation_location_to_structure(allen_id_table, zip(*np.nonzero(nvol[rng[0]:rng[1]])), ann[rng[0]:rng[1]])
            srt = sorted(olist, key=lambda x: x[0], reverse=True)
            parent_list = [xx[1] for xx in srt]
            #select only subset
            parent_list=parent_list[0:no_structures_to_keep]
            nann, lst = consolidate_parents_structures_cfos(allen_id_table, ann[rng[0]:rng[1]], parent_list, verbose=True, structures=structures)
    
            #make fig
            plt.figure(figsize=(15,18))
            ax = plt.subplot(2,1,1)
            fig = plt.imshow(np.max(atl[rng[0]:rng[1]], axis=0), cmap="gray", alpha=1)
            fig.axes.get_xaxis().set_visible(False)
            fig.axes.get_yaxis().set_visible(False)
            ax.set_title("ABA structures")
            mode = scipy.stats.mode(nann, axis=0, nan_policy="omit") #### THIS IS REALLY IMPORTANT
            most = list(np.unique(mode[1][0].ravel())); most = sorted(most, reverse=True)
            ann_mode = mode[0][0]
            masked_data = np.ma.masked_where(ann_mode < 0.1, ann_mode)
            im = plt.imshow(masked_data, cmap=tab20cmap_nogray, alpha=0.8, vmin=0, vmax=255)
            patches = [mpatches.Patch(color=im.cmap(im.norm(i[0])), label="{}".format(i[1])) for i in lst]
            plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )
            ax.set_anchor("W")
    
            #pvals
            ax = plt.subplot(2,1,2)
            ax.set_title("Number of negatively correlated voxels in AP dimension")
            #modify colormap
            import matplotlib as mpl
            my_cmap = plt.cm.plasma(np.arange(plt.cm.RdBu.N))
            my_cmap[:colorbar_cutoff,:4] = 0.0
            my_cmap = mpl.colors.ListedColormap(my_cmap)
            my_cmap.set_under("w")
            #plot
            fig = plt.imshow(np.max(atl[rng[0]:rng[1]], axis=0), cmap="gray", alpha=1)
            plt.imshow(np.sum(nvol[rng[0]:rng[1]], axis=0), cmap=my_cmap, alpha=0.95, vmin=0, vmax=zstep)
            plt.colorbar()
            fig.axes.get_xaxis().set_visible(False)
            fig.axes.get_yaxis().set_visible(False)
            ax.set_anchor("W")
            #plt.tight_layout()
            ndst = os.path.join(save_dst, "negative_overlays_zstep{}".format(zstep))
            if not os.path.exists(ndst): os.mkdir(ndst)
            plt.savefig(os.path.join(ndst, "cfos_z{}-{}.pdf".format(rng[0],rng[1])), dpi=300, transparent=True)
            plt.close()
            
    return parent_list

#%%
if __name__ == "__main__":
    
    ann_pth = "/jukebox/LightSheetTransfer/atlas/allen_atlas/annotation_2017_25um_sagittal_forDVscans_16bit.tif"
    atl_pth = "/jukebox/LightSheetTransfer/atlas/allen_atlas/average_template_25_sagittal_forDVscans.tif"
    
    pth = "/jukebox/LightSheetTransfer/kelly/201908_cfos"
    subdir = "cell_region_assignment_99percentile_no_erosion_20190909"
    #combine to get all paths
    pths = listdirfull(pth, "647"); pths.sort()
#%%    
    #make clearmap style heatmaps
    for pth in pths:
        dst = make_heatmaps(pth, subdir) #subdir = directory in which cell coordinates are stored
        print("made heat map for: {}".format(pth))

#%%            
    #analysis for dorsal up brains
##############################################################################MAKE P-VALUE MAPS############################################################
    #make destination directory
    dst = "/jukebox/wang/seagravesk/lightsheet/cfos_raw_images/pooled_analysis/2019"
    pvaldst = "/jukebox/wang/seagravesk/lightsheet/cfos_raw_images/pooled_analysis/2019/pvalue_maps/"
    
    if not os.path.exists(dst): os.mkdir(dst)
    if not os.path.exists(pvaldst): os.mkdir(pvaldst)
    if not os.path.exists(pvaldst+"/dorsal_up"): os.mkdir(pvaldst+"/dorsal_up")
    
    ctrl_du_heatmaps = [os.path.join(pth, os.path.join(xx, subdir+"/cells_heatmap.tif")) for xx in os.listdir(pth) if "647" in xx and "mouse" in xx]; ctrl_du_heatmaps.sort()
    obv_du_heatmaps = [os.path.join(pth, os.path.join(xx, subdir+"/cells_heatmap.tif")) for xx in os.listdir(pth) if "647" in xx and "observ" in xx]; obv_du_heatmaps.sort()
    dmn_du_heatmaps = [os.path.join(pth, os.path.join(xx, subdir+"/cells_heatmap.tif")) for xx in os.listdir(pth) if "647" in xx and "demons" in xx]; dmn_du_heatmaps.sort()
    
    c = stat.readDataGroup(ctrl_du_heatmaps)
    o = stat.readDataGroup(obv_du_heatmaps)
    d = stat.readDataGroup(dmn_du_heatmaps)
    
    ca = np.mean(c, axis = 0)
    cstd = np.std(c, axis = 0)
        
    oa = np.mean(o, axis = 0)
    ostd = np.std(o, axis = 0)
        
    da = np.mean(d, axis = 0)
    dstd = np.std(d, axis = 0)
    
    #write
    io.writeData(os.path.join(pvaldst, "dorsal_up/control_mean.raw"), rsp.sagittalToCoronalData(ca))
    io.writeData(os.path.join(pvaldst, "dorsal_up/control_std.raw"), rsp.sagittalToCoronalData(cstd))
    
    io.writeData(os.path.join(pvaldst, "dorsal_up/observers_mean.raw"), rsp.sagittalToCoronalData(oa))
    io.writeData(os.path.join(pvaldst, "dorsal_up/observers_std.raw"), rsp.sagittalToCoronalData(ostd))
    
    io.writeData(os.path.join(pvaldst, "dorsal_up/demonstrators_mean.raw"), rsp.sagittalToCoronalData(da))
    io.writeData(os.path.join(pvaldst, "dorsal_up/demonstrators_std.raw"), rsp.sagittalToCoronalData(dstd))
    
    #Generate the p-values map
    ##########################
    #first comparison
    #pcutoff: only display pixels below this level of significance
    pvals, psign = stat.tTestVoxelization(o.astype("float"), c.astype("float"), signed = True, pcutoff = 0.05)
    
    #color the p-values according to their sign (defined by the sign of the difference of the means between the 2 groups)
    pvalsc = stat.colorPValues(pvals, psign, positive = [0,1], negative = [1,0]);
    dst = os.path.join(pvaldst, "dorsal_up/observer_v_control/pvalues_observer_v_control.tif"); makedir(os.path.dirname(dst))
    io.writeData(dst, rsp.sagittalToCoronalData(pvalsc.astype("float32")));
    
    #second comparison
    pvals, psign = stat.tTestVoxelization(d.astype("float"), c.astype("float"), signed = True, pcutoff = 0.05)
    pvalsc = stat.colorPValues(pvals, psign, positive = [0,1], negative = [1,0]);
    dst = os.path.join(pvaldst, "dorsal_up/demonstrator_v_control/pvalues_demonstrator_v_control.tif"); makedir(os.path.dirname(dst))
    io.writeData(dst, rsp.sagittalToCoronalData(pvalsc.astype("float32")))
    
    #third comparison
    pvals, psign = stat.tTestVoxelization(d.astype("float"), o.astype("float"), signed = True, pcutoff = 0.05)
    pvalsc = stat.colorPValues(pvals, psign, positive = [0,1], negative = [1,0]);
    dst = os.path.join(pvaldst, "dorsal_up/demonstrator_v_observer/pvalues_demonstrator_v_observer.tif"); makedir(os.path.dirname(dst))
    io.writeData(dst, rsp.sagittalToCoronalData(pvalsc.astype("float32")))

##########################################################################END OF SCRIPT THAT MAKES P-VALUE MAPS###########################################################
#%%
##########################################################################LOOK AT P-VALUE MAPS IN 2D###########################################################
#set destination of p value map you want to analyze
#FIXME: look into problems w allen id table for making the ontology
allen_id_table = "/jukebox/LightSheetTransfer/atlas/ls_id_table_w_voxelcounts_16bit.xlsx" #the allen id table for this function just does not work
dorsal = os.path.join(pvaldst, "dorsal_up")

#demonstrator vs control
src = os.path.join(dorsal, "demonstrator_v_control/pvalues_demonstrator_v_control.tif")
save_dst = os.path.dirname(src)
#make parent list and 2d overlays
make_2D_overlay_of_heatmaps(src, atl_pth, ann_pth, allen_id_table, save_dst, positive = True, negative = True)

src = os.path.join(dorsal, "observer_v_control/pvalues_observer_v_control.tif")
save_dst = os.path.dirname(src)
make_2D_overlay_of_heatmaps(src, atl_pth, ann_pth, allen_id_table, save_dst, positive = True, negative = True)

src = os.path.join(dorsal,"demonstrator_v_observer/pvalues_demonstrator_v_observer.tif")
save_dst = os.path.dirname(src)
make_2D_overlay_of_heatmaps(src, atl_pth, ann_pth, allen_id_table, save_dst, positive = True, negative = True)

#%%        
#get significant structures by order    
p_val_maps = [
        listdirfull(os.path.join(dorsal, "observer_v_control"), "tif")[0],
        listdirfull(os.path.join(dorsal, "demonstrator_v_observer"), "tif")[0], 
        listdirfull(os.path.join(dorsal, "demonstrator_v_control"), "tif")[0]
        ]

atl = tifffile.imread(atl_pth)
ann = tifffile.imread(ann_pth)

atl = np.rot90(np.transpose(atl, [1, 0, 2]), axes = (2,1)) #sagittal to coronal
ann = np.rot90(np.transpose(ann, [1, 0, 2]), axes = (2,1)) #sagittal to coronal

df = pd.DataFrame()

for src in p_val_maps:
    print(src)
    
    vol = tifffile.imread(src)
    #positive correlation
    pvol = vol[:,:,:,1]
    
    pix_values = list(np.unique(ann.ravel().astype("float64")))
    
    #collect names of parents OR ##optionally get sublist
    #make structures to find parents
    structures = make_structure_objects(allen_id_table)
    parent_list = list(set([yy.parent[1] for xx in pix_values for yy in structures if xx == yy.idnum]))
    
    #find counts of highest labeled areas
    olist = annotation_location_to_structure(allen_id_table, args=zip(*np.nonzero(pvol)), ann=ann)
    srt = sorted(olist, key=lambda x: x[0], reverse=True)
    parent_list = [xx[1] for xx in srt]
    
    if "dorsal" in src:
        column_name = os.path.basename(src)[8:-4]+"_dorsal_up_positive_corr"
    else:
        column_name = os.path.basename(src)[8:-4]+"_ventral_up_positive_corr"
        
    df[column_name] = pd.Series(parent_list)
    #negative correlation            
    nvol = vol[:,:,:,0]
    pix_values = list(np.unique(ann.ravel().astype("float64")))

    structures = make_structure_objects(allen_id_table)
    parent_list = list(set([yy.parent[1] for xx in pix_values for yy in structures if xx == yy.idnum]))
    
    olist = annotation_location_to_structure(allen_id_table, args=zip(*np.nonzero(nvol)), ann=ann)
    srt = sorted(olist, key=lambda x: x[0], reverse=True)
    parent_list = [xx[1] for xx in srt]
    
    if "dorsal" in src:
        column_name = os.path.basename(src)[8:-4]+"_dorsal_up_negative_corr"
    else:
        column_name = os.path.basename(src)[8:-4]+"_ventral_up_negative_corr"
    
    df[column_name] = pd.Series(parent_list)

#save out
dfdst = os.path.join(pvaldst, "significant_structures_based_on_pvalue_maps.xlsx")       
df.to_excel(dfdst, index = None)
    
    
