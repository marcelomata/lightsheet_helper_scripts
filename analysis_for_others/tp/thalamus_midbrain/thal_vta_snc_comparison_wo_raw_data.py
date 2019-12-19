#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 14:44:22 2019

@author: wanglab
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np, os, pickle as pckl
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42

#import data
pth = "/jukebox/wang/zahra/modeling/h129/vta_snc/mean_count_and_density_data_contra.p"
data = pckl.load(open(pth, "rb"), encoding = "latin1")

#set dst 
dst = "/home/wanglab/Desktop"
#dst = '/Users/tjp7rr1/Downloads'

cell_counts_per_brain = data["cell_counts_per_brain"]
brains = data["brainnames"]
ak_pool = data["ak_pool"]
primary_pool = data["primary_pool"]
short_nuclei = data["short_nuclei"]
density_per_brain = data["density_per_brain"]
primary_lob_n = data["primary_lob_n"]


## mean density
fig = plt.figure(figsize=(5,2))
ax = fig.add_axes([.4,.1,.5,.8])

mean_density = np.asarray([np.mean(density_per_brain[np.where(primary_pool == idx)[0]], axis=0) for idx in np.unique(primary_pool)])

show = mean_density.astype(int).T #np.flip(mean_counts, axis = 1) # NOTE abs

vmin = 0
vmax = 75
cmap = plt.cm.viridis
cmap.set_over('gold')
#colormap
# discrete colorbar details
bounds = np.linspace(vmin,vmax,6)
#bounds = np.linspace(-2,5,8)
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

pc = ax.pcolor(show, cmap=cmap, vmin=vmin, vmax=vmax)#, norm=norm)
cb = plt.colorbar(pc, ax=ax, cmap=cmap, norm=norm, spacing="proportional", 
                  ticks=bounds, boundaries=bounds, format="%d", shrink=0.5, aspect=10)
cb.set_label("Cells/$mm^3$", fontsize="small", labelpad=2)
cb.ax.tick_params(labelsize="small")

cb.ax.set_visible(True)
# exact value annotations
for ri,row in enumerate(show):
    for ci,col in enumerate(row):
        pass
        if col < 20:
            ax.text(ci+.5, ri+.5, "{:d}".format(col), color="white", ha="center", va="center", fontsize="small")
        else:
            ax.text(ci+.5, ri+.5, "{:d}".format(col), color="k", ha="center", va="center", fontsize="small")
        
#remaking labeles so it doesn't look squished
ax.set_xticks(np.arange(len(ak_pool))+.5)
lbls = np.asarray(ak_pool)
ax.set_xticklabels(["{}\nn = {}".format(ak, n) for ak, n in zip(ak_pool, primary_lob_n)], rotation=45, fontsize=7, ha="right")
# yticks
ax.set_yticks(np.arange(len(short_nuclei))+.5)

ax.set_yticklabels(["{}".format(bi) for bi in short_nuclei], fontsize="small")

plt.savefig(os.path.join(dst,"thalvtacomp_mean_density.pdf"), bbox_inches = "tight")


## mean counts
fig = plt.figure(figsize=(5,2))
ax = fig.add_axes([.4,.1,.5,.8])

mean_counts = np.asarray([np.mean(cell_counts_per_brain[np.where(primary_pool == idx)[0]], axis=0) for idx in np.unique(primary_pool)])

show = mean_counts.astype(int).T #np.flip(mean_counts, axis = 1) # NOTE abs

vmin = 0
vmax = 50
cmap = plt.cm.viridis
cmap.set_over('gold')
#colormap
# discrete colorbar details
bounds = np.linspace(vmin,vmax,6)
#bounds = np.linspace(-2,5,8)
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

pc = ax.pcolor(show, cmap=cmap, vmin=vmin, vmax=vmax)#, norm=norm)
cb = plt.colorbar(pc, ax=ax, cmap=cmap, norm=norm, spacing="proportional", 
                  ticks=bounds, boundaries=bounds, format="%d", shrink=0.5, aspect=10)
cb.set_label("Count", fontsize="small", labelpad=2)
cb.ax.tick_params(labelsize="small")

cb.ax.set_visible(True)
# exact value annotations
for ri,row in enumerate(show):
    for ci,col in enumerate(row):
        pass
        if col < 30:
            ax.text(ci+.5, ri+.5, "{:d}".format(col), color="white", ha="center", va="center", fontsize="small")
        else:
            ax.text(ci+.5, ri+.5, "{:d}".format(col), color="k", ha="center", va="center", fontsize="small")
        
#remaking labeles so it doesn't look squished
ax.set_xticks(np.arange(len(ak_pool))+.5)
lbls = np.asarray(ak_pool)
ax.set_xticklabels(["{}\nn = {}".format(ak, n) for ak, n in zip(ak_pool, primary_lob_n)], rotation=45, fontsize=7, ha="right")
# yticks
ax.set_yticks(np.arange(len(short_nuclei))+.5)

ax.set_yticklabels(["{}".format(bi) for bi in short_nuclei], fontsize="small")

plt.savefig(os.path.join(dst,"thalvtacomp_mean_counts.pdf"), bbox_inches = "tight")
#%%