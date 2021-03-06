# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 13:52:54 2020

@author: wanglab
"""

import numpy as np, os, matplotlib.pyplot as plt, tifffile, pandas as pd, seaborn as sns, SimpleITK as sitk
from collections import Counter
os.chdir("/jukebox/wang/zahra/python/BrainPipe")
from tools.analysis.network_analysis import make_structure_objects

#set appropriate pth
src = "/jukebox/wang/zahra/kelly_cell_detection_analysis"
erode_pth = os.path.join(src, "annotation_allen_2017_25um_sagittal_erode_80um.tif")
dilate_pth = os.path.join(src, "dilated_atlases")

fig_dst = "/home/wanglab/Desktop"
df_pth = "/jukebox/LightSheetTransfer/atlas/allen_atlas/allen_id_table_w_voxel_counts_16bit.xlsx"
ann_pth = "/jukebox/LightSheetTransfer/atlas/allen_atlas/annotation_2017_25um_sagittal_forDVscans_16bit.tif"

#%%
#read vols
ann = sitk.GetArrayFromImage(sitk.ReadImage(ann_pth))
df = pd.read_excel(df_pth)
er_ann = tifffile.imread(erode_pth)
dl_anns = [os.path.join(dilate_pth, xx) for xx in os.listdir(dilate_pth)]

org_iids = np.unique(ann)[1:] #excluding 0
er_iids = np.unique(er_ann)[1:]

missing = [iid for iid in org_iids if iid not in er_iids]

missing_struct_names = [nm for nm in df.name.values if df.loc[df.name == nm, "id"].values[0] in missing] #excluding root
missing_struct_voxels = [df.loc[df.name == nm, "voxels_in_structure"].values[0] for nm in missing_struct_names]
#replace id column that matches to names
missing_struct_ids = [df.loc[df.name == nm, "id"].values[0] for nm in missing_struct_names]

#get parent names
missing_struct_parents = [df.loc[df["id"] == iid, "parent_name"].values[0]
                          for iid in missing_struct_ids]

#%%
#plot results
#barplot of areas most represented by missing structures
unq_structs = np.unique(np.array(missing_struct_parents))
heights = np.array([v for k,v in dict(Counter(np.array(missing_struct_parents))).items()])

#remove those only represented once
heights_gr1 = heights[heights > 1]
unq_structs_gr1 = unq_structs[heights > 1]

plt.figure(figsize=(11, 6))
plt.bar(x = unq_structs_gr1, height = heights_gr1)
plt.xticks(unq_structs_gr1, rotation=30, fontsize="xx-small", ha="right")
plt.yticks(np.unique(heights))
plt.ylabel("Number of child structures eroded")
plt.xlabel("Parent regions")
plt.savefig(os.path.join(fig_dst, "parent_structures_eroded_80um_barplot.pdf"), bbox_inches = "tight")

#%%
#correlation between # of voxels in the structure in original volume, vs. in eroded volume

all_struct_voxels = [len(np.where(ann == iid)[0]) for iid in org_iids]
er_struct_voxels = [len(np.where(er_ann == iid)[0]) for iid in org_iids]
all_struct_nms = [df.loc[df["id"] == iid, "name"].values[0] for iid in org_iids] #excluding root

#%%
plt.scatter(x = np.array(all_struct_voxels) , y = np.array(er_struct_voxels))
plt.plot(np.array(all_struct_voxels), np.array(all_struct_voxels), color = "gray", linestyle = "dashdot", linewidth = 1) # identity line
plt.ylabel("Voxels in 80um eroded volume")
plt.xlabel("Voxels in original volume")
plt.savefig(os.path.join(fig_dst, "voxels_scatter_org_vs_eroded.pdf"), bbox_inches = "tight")

#%%
#zoom
plt.scatter(x = np.array(all_struct_voxels) , y = np.array(er_struct_voxels))
plt.plot(np.array(all_struct_voxels), np.array(all_struct_voxels), color = "gray", linestyle = "dashdot", linewidth = 1) # identity line
plt.ylabel("Voxels in 80um eroded volume")
plt.xlabel("Voxels in original volume")
plt.xlim([0,250000]);plt.ylim([0, 150000])
plt.savefig(os.path.join(fig_dst, "voxels_scatter_org_vs_eroded_250000_voxels.pdf"), bbox_inches = "tight")

#%%

missing_struct_voxels_sort = np.sort(np.array(missing_struct_voxels))
missing_struct_names_sort = np.array(missing_struct_names)[np.argsort(np.array(missing_struct_voxels))]

df = pd.DataFrame()
df["num_voxels"] = missing_struct_voxels+all_struct_voxels
df["type"] = ["eroded"]*len(missing_struct_voxels) + ["original"]*len(all_struct_voxels)

sns.stripplot(x = "num_voxels", y = "type", data = df,  color = "crimson", orient = "h")
sns.boxplot(x = "num_voxels", y = "type", data = df, orient = "h", showfliers=False, showcaps=False, 
            boxprops={'facecolor':'None'})
plt.xlim([0, 200000])
plt.xlabel("Total number of voxels in structure")
plt.ylabel("Structures 'zero'ed' out vs. all original structures")
plt.savefig(os.path.join(fig_dst, "boxplot_total_voxels_org_vs_eroded.pdf"), bbox_inches = "tight")

#%%
#export missing structures name, id, and total voxel count

dataf = pd.DataFrame()
dataf["name"] = missing_struct_names
dataf["id"] = missing_struct_ids
dataf["parent_name"] = missing_struct_parents
dataf["voxels_in_structure"] = missing_struct_voxels

dataf.to_csv(os.path.join(src, "structures_zeroed_after_80um_erosion_allen_annotation_2017_ids_fixed_v2.csv"))

#%%

#make a volume where only the "zeroed" out structures are displayed, zero out the rest
zr_ann = ann.copy()
for iid in missing:
    zr_ann[zr_ann == iid] = 0

tifffile.imsave(r"Z:\zahra\kelly_cell_detection_analysis\non_zeroed_out_structures_in_org_atlas_for_vis.tif", zr_ann)    
