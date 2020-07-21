#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 21 16:01:17 2020

@author: wanglab
"""

import sys,os
sys.path.append("/jukebox/wang/zahra/python/BrainPipe")
from tools.registration.register import elastix_command_line_call

mv = "/jukebox/LightSheetTransfer/kelly/2020_07_15/20200715_12_14_06_f37080_mouse2_20171015/Ex_488_Em_0/downsized_for_atlas.tif"
fx = "/jukebox/LightSheetTransfer/atlas/allen_atlas/average_template_25_sagittal_forDVscans.tif"

out = "/jukebox/LightSheetTransfer/kelly/2020_07_15/20200715_12_14_06_f37080_mouse2_20171015/elastix"
if not os.path.exists(out): os.mkdir(out)

param_fld = "/jukebox/wang/zahra/python/BrainPipe/parameterfolder"
params = [os.path.join(param_fld, xx) for xx in os.listdir(param_fld)]

e_out, transformfiles = elastix_command_line_call(fx, mv, out, params)
