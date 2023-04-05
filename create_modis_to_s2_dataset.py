
import os
import numpy as np
from imageio import imread, imsave
import matplotlib.pyplot as plt
import tifffile as tiff
from pathlib import Path
import shutil


s2_dir = Path("D:/wildfire-s1s2-dataset-ca-modis-250m/S2")
modis_dir = Path("D:/wildfire-s1s2-dataset-ca-modis")

s2_post_list = os.listdir(s2_dir / 'post')
modis_post_list = os.listdir(modis_dir / 'mask' / 'modis')

common_list = set(s2_post_list).intersection(set(modis_post_list))
print(len(common_list))

for filename in s2_post_list:
    if filename not in common_list:
        # remove to folder "deleted"
        print(filename)
        # shutil.move(str(modis_dir / 'post' / filename), str(modis_dir / 'post-deleted'))

        os.remove(str(modis_dir / 'mask' / 'modis' / filename))
        os.remove(str(modis_dir / 'modis' / 'post' / filename))

# # obtain final modis list
# modis_final_list = os.listdir("D:\wildfire-s1s2-dataset-ca-modis-250m-check\modis\post")
# filelist = []
# for filename in modis_final_list:
#     filelist.append(filename[:-4])

# print(len(filelist))

# src_dir = modis_dir
# for tiff_name in modis_post_list:
#     if tiff_name[:-4] not in filelist:
#         print(tiff_name)
#         # os.remove(str(src_dir / 'mask' / 'firecci' / tiff_name))
#         shutil.move(str(src_dir / 'mask' / 'firecci' / tiff_name), str(src_dir / 'mask' / 'firecci-deleted'))