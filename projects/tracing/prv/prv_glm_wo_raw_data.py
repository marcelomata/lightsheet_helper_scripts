#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 16:02:15 2019

@author: wanglab
"""

import matplotlib as mpl, os
import matplotlib.pyplot as plt
import numpy as np, pickle as pckl


mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42

#imports
#path to pickle file
data_pth = "/jukebox/wang/zahra/tracing_projects/prv/for_tp/model_data_contra_pma.p"
data = pckl.load(open(data_pth, "rb"), encoding = "latin1")

#set dest
dst = "/jukebox/wang/zahra"
#dst = "/Users/tjp7rr1/Downloads"

#set the appropritate variables
c_mat = data["c_mat"]
mat = data["mat"]
pmat = np.asarray(data["pmat"])
p_shuf = np.asarray(data["p_shuf"])
mat_shuf = np.asarray(data["mat_shuf"])
ak_pool = data["ak_pool"]
regions = data["regions"]
primary_lob_n = data["primary_lob_n"]

#shortened lables for figures
regions = np.array(["IL, PL, \nAC, ORB", "AI", "GU, VISC", "MO, SS", "RSP", "VIS", "PTLp",
                    "TEa, AUD", "PERI, ECT"])

## display
fig = plt.figure(figsize=(6,5))
ax = fig.add_axes([.4,.1,.5,.8])

#set white text limit here
whitetext = 8
annotation_size = "medium"#annotation/number sizes

vmin = 0
vmax = 10
cmap = plt.cm.Reds
cmap.set_under("w")
cmap.set_over("maroon")

#tp local
tp = True
if tp:
#    dst = "/Users/tjp7rr1/Downloads"
    vmin = 0
    vmax = 5
    cmap = plt.cm.Blues#plt.cm.Reds
    cmap.set_over(plt.cm.Blues(1.0)) #cmap.set_over("maroon")
    whitetext = 4
    cmap.set_under("w")

# map 1: weights
show = np.flipud(mat) # NOTE abs

#colormap
# discrete colorbar details
pc = ax.pcolor(show, cmap=cmap, vmin=vmin, vmax=vmax)
cb = plt.colorbar(pc, ax=ax, cmap=cmap, format="%d", shrink=0.3, aspect=10)
cb.set_label("Weight / SE", fontsize="small", labelpad=3)
cb.ax.tick_params(labelsize="x-small")

cb.ax.set_visible(True)

#annotations
for ri,row in enumerate(show): 
    for ci,col in enumerate(row):
        if col > whitetext:
            ax.text(ci+.5, ri+.5, "{:0.1f}".format(col), color="white", ha="center", va="center", fontsize=annotation_size)
        else:
            ax.text(ci+.5, ri+.5, "{:0.1f}".format(col), color="k", ha="center", va="center", fontsize=annotation_size)   
            
# signif
sig = np.flipud(pmat) < .05#/np.size(pmat)
p_shuf_pos = np.where(mat_shuf < 0, p_shuf, p_shuf*10)
null = (p_shuf_pos < .05).sum(axis=(1,2))
nullmean = null.mean()
nullstd = null.std()
for y,x in np.argwhere(sig):
    pass
    ax.text(x, y+0.3, "*", fontsize=10, ha="left", va="bottom", color = "white", transform=ax.transData)

# aesthetics
ax.set_xticks(np.arange(len(ak_pool))+.5)
lbls = np.asarray(ak_pool)
ax.set_xticklabels(lbls, rotation=30, fontsize="x-small", ha="right")
# yticks
ax.set_yticks(np.arange(len(regions))+.5)
ax.set_yticklabels(["{}".format(bi) for bi in np.flipud(regions)], fontsize="medium")

#despline to make it look similar to paper figure
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.grid(False)
ax.tick_params(length=6)

plt.savefig(os.path.join(dst, "prv_nc_glm_contra_layer56_pma.pdf"), bbox_inches = "tight")
#%%
