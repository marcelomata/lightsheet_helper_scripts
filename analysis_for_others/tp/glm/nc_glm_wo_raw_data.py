#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 17 18:21:39 2019

@author: wanglab
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np, os, pickle as pckl
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
#imports
#path to pickle file
data_pth = "/jukebox/wang/zahra/modeling/h129/neocortex/model_data_contra_pma.p"
#data_pth = "/jukebox/wang/zahra/modeling/h129/neocortex/model_data_contra.p"
data = pckl.load(open(data_pth, "rb"), encoding = "latin1")

#raw data
raw_data_pth = "/jukebox/wang/zahra/modeling/h129/neocortex/data_v2.p"
raw = pckl.load(open(raw_data_pth, "rb"), encoding = "latin1")

#set the appropritate variables
c_mat = data["c_mat"]
mat = data["mat"]
pmat = np.asarray(data["pmat"])
p_shuf = np.asarray(data["p_shuf"])
mat_shuf = np.asarray(data["mat_shuf"])
ak_pool = data["ak_pool"]
regions = data["regions"]
primary_lob_n = data["primary_lob_n"]
cell_counts_per_brain_p = raw["cell_counts_per_brain"]
primary_pool = raw["primary_pool"]

dst = "/home/wanglab/Desktop"


#tp local
tp = True
if tp:
    dst = "/Users/tjp7rr1/Downloads"
    vmin = 0
    vmax = 4
    cmap = plt.cm.Blues#plt.cm.Reds
    cmap.set_over(plt.cm.Blues(1.0)) #cmap.set_over('maroon')
    whitetext = 6
    cmap.set_under('w')
    #reorder xaxis
    pmat = np.concatenate([pmat[:,:3], pmat[:,3:][:,::-1]], 1)
    ak_pool = np.concatenate([ak_pool[:3], ak_pool[3:][::-1]], 0)
    
    #TP NOTE - FOR SOME REASON THIS MESSES UP SIGNIFICANT ASTERISKS, numbers are ok
    #LOOK AT ZAHRAS FOR THAT

else:
    vmin = 0
    vmax = 8
    whitetext = 6
    cmap = plt.cm.Reds
    cmap.set_under("w")
    cmap.set_over("maroon")

## display
fig = plt.figure(figsize=(5,5))
ax = fig.add_axes([.4,.1,.5,.8])

# map 1: weights
show = np.flipud(mat) # NOTE abs
if tp: show = np.concatenate([show[:,:3], show[:,3:][:,::-1]], 1)

#colormap
# discrete colorbar details
bounds = np.linspace(vmin,vmax,(vmax-vmin)/2 + 1)
if tp: bounds = np.linspace(vmin,vmax,vmax + 1)
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
if tp: sig = np.concatenate([sig[:,:3], sig[:,3:][:,::-1]], 1)
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


#%%
#mean counts
mean_counts = np.asarray([np.mean(cell_counts_per_brain_p[np.where(primary_pool == idx)[0]], axis=0) for idx in np.unique(primary_pool)])

fig = plt.figure(figsize=(5,4))
ax = fig.add_axes([.4,.1,.5,.8])

show = np.flipud(mean_counts.T) #np.flip(mean_counts, axis = 1) # NOTE abs

vmin = 0
vmax = 20
cmap = plt.cm.viridis
cmap.set_over('gold')
#colormap
# discrete colorbar details
bounds = np.linspace(vmin,vmax,6)
#bounds = np.linspace(-2,5,8)
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

pc = ax.pcolor(show, cmap=cmap, vmin=vmin, vmax=vmax)#, norm=norm)
cb = plt.colorbar(pc, ax=ax, cmap=cmap, norm=norm, spacing="proportional", ticks=bounds, boundaries=bounds, format="%0.1f", 
                  shrink=0.3, aspect=10)
cb.set_label("Mean % of neocortex counts", fontsize="x-small", labelpad=3)
cb.ax.tick_params(labelsize="x-small")

cb.ax.set_visible(True)
# exact value annotations
for ri,row in enumerate(show):
    for ci,col in enumerate(row):
        pass
        ax.text(ci+.5, ri+.5, "{:0.1f}".format(col), color="k", ha="center", va="center", fontsize=5)
        
# aesthetics
# xticksjt -t monokai -m 200
ax.set_xticks(np.arange(len(ak_pool))+.5)

#remaking labeles so it doesn't look squished
lbls = np.asarray(ak_pool)
ax.set_xticklabels(["{}\nn = {}".format(lbl, n) for lbl, n in zip(lbls, primary_lob_n)], rotation=30, fontsize="xx-small", ha="right")
# yticks
ax.set_yticks(np.arange(len(regions))+.5)
#changing order of regions for tp to visualize
ax.set_yticklabels(["{}".format(bi) for bi in np.flip(regions)], fontsize="xx-small")
