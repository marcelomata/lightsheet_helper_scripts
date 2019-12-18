#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 18:57:00 2019

@author: wanglab
"""

from tools.analysis.network_analysis import make_structure_objects
import statsmodels.api as sm
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np, os, pickle as pckl
from skimage.external import tifffile
import pandas as pd

#custom
inj_pth = "/jukebox/wang/pisano/tracing_output/antero_4x_analysis/linear_modeling/neocortex/injection_sites"
atl_pth = "/jukebox/LightSheetTransfer/atlas/sagittal_atlas_20um_iso.tif"
ann_pth = "/jukebox/LightSheetTransfer/atlas/annotation_sagittal_atlas_20um_iso.tif"
cells_regions_pth = "/jukebox/wang/zahra/h129_contra_vs_ipsi/data/nc_contra_counts_33_brains_pma.csv"
dst = "/home/wanglab/Desktop"

#making dictionary of injection sites
injections = {}

#MAKE SURE THEY ARE IN THIS ORDER
brains = ["20180409_jg46_bl6_lob6a_04", 
          "20180608_jg75", 
          "20170204_tp_bl6_cri_1750r_03",
          "20180608_jg72", 
          "20180416_jg56_bl6_lob8_04", 
          "20170116_tp_bl6_lob45_ml_11", 
          "20180417_jg60_bl6_cri_04", 
          "20180410_jg52_bl6_lob7_05", 
          "20170116_tp_bl6_lob7_1000r_10", 
          "20180409_jg44_bl6_lob6a_02", 
          "20180410_jg49_bl6_lob45_02", 
          "20180410_jg48_bl6_lob6a_01", 
          "20180612_jg80", 
          "20180608_jg71",
          "20170212_tp_bl6_crii_1000r_02", 
          "20170115_tp_bl6_lob6a_rpv_03", 
          "20170212_tp_bl6_crii_2000r_03", 
          "20180417_jg58_bl6_sim_02",
          "20170130_tp_bl6_sim_1750r_03", 
          "20170115_tp_bl6_lob6b_ml_04", 
          "20180410_jg50_bl6_lob6b_03", 
          "20170115_tp_bl6_lob6a_1000r_02", 
          "20170116_tp_bl6_lob45_500r_12", 
          "20180612_jg77", 
          "20180612_jg76", 
          "20180416_jg55_bl6_lob8_03", 
          "20170115_tp_bl6_lob6a_500r_01", 
          "20170130_tp_bl6_sim_rpv_01", 
          "20170204_tp_bl6_cri_1000r_02", 
          "20170212_tp_bl6_crii_250r_01", 
          "20180417_jg61_bl6_crii_05",
          "20170116_tp_bl6_lob7_ml_08", 
          "20180409_jg47_bl6_lob6a_05"]

for pth in brains:
    print(pth)
    pth = os.path.join(inj_pth, pth+".tif.tif")
    injection = tifffile.imread(pth)
    print(injection.shape)
    injections[os.path.basename(pth)[:-8]] = injection #files have 2 .tif in the end
    
inj_raw = np.array([inj.astype(bool) for nm, inj in injections.items()])
    
atl_raw = tifffile.imread(atl_pth)
ann_raw = tifffile.imread(ann_pth)[:, 423:, :] #apparent cutoff
anns = np.unique(ann_raw).astype(int)
print(ann_raw.shape)

#annotation IDs of the cerebellum ONLY that are actually represented in annotation file
iids = {"Lingula (I)": 912,
        "Lobule II": 976,
        "Lobule III": 984,
        "Lobule IV-V": 1091,
        "Lobule VIa": 936,
        "Lobule VIb": 1134,
        "Lobule VII": 944,
        "Lobule VIII": 951,
        "Lobule IX": 957, #uvula IX
        "Lobule X": 968, #nodulus X
        "Simplex lobule": 1007, #simplex
        "Crus 1": 1056, #crus 1
        "Crus 2": 1064, #crus 2
        "Paramedian lobule": 1025, #paramedian lob
        "Copula pyramidis": 1033 #copula pyramidis
        }
ak = np.asarray([k for k,v in iids.items()])

atlas_rois = {}
for nm, iid in iids.items():
    z,y,x = np.where(ann_raw == iid) #find where structure is represented
    ann_blank = np.zeros_like(ann_raw)
    ann_blank[z,y,x] = 1 #make a mask of structure in annotation space
    atlas_rois[nm] = ann_blank.astype(bool) #add mask of structure to dictionary

expr_all_as_frac_of_lob = np.array([[(mouse.ravel()[lob.ravel()].astype(int)).sum() / lob.sum() for nm, lob in atlas_rois.items()] for mouse in inj_raw])    
expr_all_as_frac_of_inj = np.array([[(mouse.ravel()[lob.ravel()].astype(int)).sum() / mouse.sum() for nm, lob in atlas_rois.items()] for mouse in inj_raw])    
primary = np.array([np.argmax(e) for e in expr_all_as_frac_of_inj])
primary_as_frac_of_lob = np.array([np.argmax(e) for e in expr_all_as_frac_of_lob])
secondary = np.array([np.argsort(e)[-2] for e in expr_all_as_frac_of_inj])

#%%

#pooled injections
ak_pool = np.asarray(["Lob. I-III, IV-V", "Lob. VIa, VIb, VII", "Lob. VIII, IX, X",
                 "Simplex", "Crura", "PM, CP"])

#pooling injection regions
expr_all_as_frac_of_lob_pool = np.asarray([[brain[0]+brain[1]+brain[2]+brain[3], brain[4]+brain[5]+brain[6], 
                                 brain[7]+brain[8]+brain[9],brain[10], brain[11]+brain[12], 
                                 brain[13]+brain[14]] for brain in expr_all_as_frac_of_lob])

expr_all_as_frac_of_inj_pool = np.asarray([[brain[0]+brain[1]+brain[2]+brain[3], brain[4]+brain[5]+brain[6], 
                                 brain[7]+brain[8]+brain[9],brain[10], brain[11]+brain[12], 
                                 brain[13]+brain[14]] for brain in expr_all_as_frac_of_inj])
    
primary_pool = np.array([np.argmax(e) for e in expr_all_as_frac_of_inj_pool])

#get n"s after pooling
primary_lob_n = np.asarray([np.where(primary_pool == i)[0].shape[0] for i in np.unique(primary_pool)])

#normalization  of inj site
expr_all_as_frac_of_inj_pool_norm = np.asarray([brain/brain.sum() for brain in expr_all_as_frac_of_inj_pool])

#%%

#making dictionary of cells by region
cells_regions = pd.read_csv(cells_regions_pth)
#rename structure column
cells_regions["Structure"] = cells_regions["Unnamed: 0"]
cells_regions = cells_regions.drop(columns = ["Unnamed: 0"])
#pooling regions
structures = make_structure_objects("/jukebox/LightSheetTransfer/atlas/allen_atlas/allen_id_table_w_voxel_counts.xlsx", 
                                    remove_childless_structures_not_repsented_in_ABA = True, ann_pth=ann_pth)


#GET ONLY NEOCORTICAL POOLS
sois = ["Infralimbic area", "Prelimbic area", "Anterior cingulate area", "Frontal pole, cerebral cortex", "Orbital area", 
            "Gustatory areas", "Agranular insular area", "Visceral area", "Somatosensory areas", "Somatomotor areas",
            "Retrosplenial area", "Posterior parietal association areas", "Visual areas", "Temporal association areas",
            "Auditory areas", "Ectorhinal area", "Perirhinal area"]

#make new dict - for all brains
cells_pooled_regions = {} #for raw counts

for brain in brains:    
    #make new dict - this is for EACH BRAIN
    c_pooled_regions = {}
    
    for soi in sois:
        counts = []
        try:
            soi = [s for s in structures if s.name==soi][0]
            counts.append(cells_regions.loc[cells_regions.Structure == soi.name, brain].values[0]) #store counts in this list
            #add to volume list from LUT
            progeny = [str(xx.name) for xx in soi.progeny]
            #now sum up progeny
            if len(progeny) > 0:
                for progen in progeny:
                    counts.append(cells_regions.loc[cells_regions.Structure == progen, brain].values[0])
                            #add to volume list from LUT
            c_pooled_regions[soi.name] = np.sum(np.asarray(counts))
        except:
            counts.append(cells_regions.loc[cells_regions.Structure == soi, brain].values[0])                    
            c_pooled_regions[soi] = np.sum(np.asarray(counts))
    #add to big dict
    cells_pooled_regions[brain] = c_pooled_regions

#making the proper array per brain where regions are removed
cell_counts_per_brain = []

#initialise dummy var
i = []
for k,v in cells_pooled_regions.items():
    dct = cells_pooled_regions[k]
    for j,l in dct.items():
        i.append(l)  
    cell_counts_per_brain.append(i)
    #re-initialise for next
    i = []  
    
cell_counts_per_brain = np.asarray(cell_counts_per_brain)
#make into % counts the proper way
pcounts = np.asarray([((brain/np.sum(brain))*100) for brain in cell_counts_per_brain])    

#%%

pcounts_pool = np.asarray([[brain[0]+brain[1]+brain[2]+brain[4], brain[3], brain[6], brain[5]+brain[7], 
                                          brain[8]+brain[9], brain[10], brain[12], brain[11], 
                                          brain[13]+brain[14], brain[15]+brain[16]] for brain in pcounts])


regions = np.asarray(["Infralimbic, Prelimbic,\n Ant. Cingulate, Orbital",
       "Frontal pole", "Agranular insula", "Gustatory, Visceral",
       "Somatomotor, Somatosensory", "Retrosplenial", "Visual",
       "Post. parietal", "Temporal, Auditory", "Peririhinal, Ectorhinal"])
    
    
X = expr_all_as_frac_of_inj_pool_norm
Y = pcounts_pool    

#%%

##  glm
c_mat = []
mat = []
pmat = []
mat_shuf = []
p_shuf = []
fit = []
fit_shuf = []

for itera in range(1000):
    if itera%100 == 0: print(itera)
    if itera == 0:
        shuffle = False
        inj = X.copy()
    else:
        shuffle = True
        mat_shuf.append([])
        p_shuf.append([])
        fit_shuf.append([])
        inj = X[np.random.choice(np.arange(len(inj)), replace=False, size=len(inj)),:]
    for count, region in zip(Y.T, regions):
        inj_ = inj[~np.isnan(count)]
        count = count[~np.isnan(count)]

        # intercept:
        inj_ = np.concatenate([inj_, np.ones(inj_.shape[0])[:,None]*1], axis=1)
        
#        glm = sm.OLS(count, inj_)
        glm = sm.GLM(count, inj_, family=sm.families.Poisson())
        res = glm.fit()
        
        coef = res.params[:-1]
        se = res.bse[:-1]
        pvals = res.pvalues[:-1] 

        val = coef/se

        if not shuffle:
            c_mat.append(coef)
            mat.append(val)
            pmat.append(pvals)
            fit.append(res.fittedvalues)
            
        elif shuffle:
            mat_shuf[-1].append(val)
            p_shuf[-1].append(pvals)
            fit_shuf[-1].append(res.fittedvalues)
        # inspect residuals
        """
        if not shuffle:
            plt.clf()
            plt.scatter(res.fittedvalues, res.resid)
            plt.hlines(0, res.fittedvalues.min(), res.fittedvalues.max())
            plt.title(region)
            plt.xlabel("Fit-vals")
            plt.ylabel("Residuals")
            plt.savefig(os.path.join(dst, "resid_inspection-{}.png").format(region))
        """
        
c_mat = np.array(c_mat)
mat = np.array(mat) # region x inj
mat_shuf = np.array(mat_shuf) # region x inj
pmat = np.array(pmat) # region x inj
p_shuf = np.array(p_shuf)
fit = np.array(fit)
fit_shuf = np.array(fit_shuf)

#%%

## display
fig = plt.figure(figsize=(5,5))
ax = fig.add_axes([.4,.1,.5,.8])

# map 1: weights
show = np.flipud(mat) # NOTE abs

vmin = 1
vmax = 6
whitetext = 4
cmap = plt.cm.Reds
cmap.set_under("w")
cmap.set_over("maroon")
#colormap
# discrete colorbar details
bounds = np.linspace(vmin,vmax,(vmax-vmin) + 1)
#bounds = np.linspace(0,5,11)
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

pc = ax.pcolor(show, cmap=cmap, vmin=vmin, vmax=vmax, norm=norm)
cb = plt.colorbar(pc, ax=ax, cmap=cmap, norm=norm, spacing="proportional", ticks=bounds, boundaries=bounds, format="%0.1f", 
                  shrink=0.3, aspect=10)
cb.set_label("Weight / SE", fontsize="x-small", labelpad=3)
cb.ax.tick_params(labelsize="x-small")

cb.ax.set_visible(True)

# exact value annotations
for ri,row in enumerate(show):
    for ci,col in enumerate(row):
        if col < whitetext:
            ax.text(ci+.5, ri+.5, "{:0.1f}".format(col), color="k", ha="center", va="center", fontsize="small")
        else: 
            ax.text(ci+.5, ri+.5, "{:0.1f}".format(col), color="white", ha="center", va="center", fontsize="small")

# signif
sig = np.flipud(pmat) < .05#/np.size(pmat)
p_shuf_pos = np.where(mat_shuf < 0, p_shuf, p_shuf*10)
null = (p_shuf_pos < .05).sum(axis=(1,2))
nullmean = null.mean()
nullstd = null.std()
for y,x in np.argwhere(sig):
    pass
    ax.text(x, y+0.3, "*", fontsize=10, ha="left", va="bottom", color = "black", transform=ax.transData)
#ax.text(.5, 1.06, "X: p<0.05".format(nullmean, nullstd), ha="center", va="center", fontsize="small", transform=ax.transAxes)
ax.text(.5, 1.06, "*: p<0.05\n{:0.1f} ($\pm$ {:0.1f}) *'s are expected by chance if no real effect exists".format(nullmean, nullstd), ha="center", va="center", fontsize="x-small", transform=ax.transAxes)

# aesthetics
# xticksjt -t monokai -m 200
ax.set_xticks(np.arange(len(ak_pool))+.5)

#remaking labeles so it doesn"t look squished
lbls = np.asarray(ak_pool)
ax.set_xticklabels(["{}\nn = {}".format(ak, n) for ak, n in zip(lbls, primary_lob_n)], rotation=30, fontsize=6, ha="right")
# yticks
ax.set_yticks(np.arange(len(regions))+.5)
ax.set_yticklabels(["{}".format(bi) for bi in np.flipud(regions)], fontsize="small")
plt.savefig(os.path.join(dst, "nc_glm.pdf"), bbox_inches = "tight")