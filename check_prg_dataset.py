
import os
import numpy as np
from imageio import imread, imsave
import tifffile as tiff
from pathlib import Path
import matplotlib.pyplot as plt
from astropy.visualization import PercentileInterval
interval_98 = PercentileInterval(98)

bucket = "wildfire-prg-dataset-v1"
rootPath = Path(f"D:\{bucket}")
vis_dict = {
    # 'ALOS': [0, 1, 2],
    'S1': [0, 1, 2],
    # 'S2': [9, 6, 2], # B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12, cloud
    'S2': [5, 3, 2], # B2, B3, B4, B8, B11, B12
    # 'S2': [2, 1, 0], # B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12, cloud
    # 'mask': 0,
    # 'AUZ': 0
}

for event in ["CA2021CrissCreek"]:
# for event in os.listdir(rootPath):
    for sat in os.listdir(rootPath / event):
        for filename in os.listdir(rootPath / event / sat):

            save_dir = Path("D:/") / f"{bucket}-check" / event / sat
            if not os.path.exists(save_dir): os.makedirs(save_dir)
            dst_url =  save_dir / f"{filename[:-4]}.png"

            image = tiff.imread(rootPath / event / sat / filename)

            print(dst_url)
            print(image.shape)

            if sat in ['mask', 'AUZ']: plt.imsave(dst_url, interval_98(image), vmin=0, vmax=1)
            else: plt.imsave(dst_url, interval_98(image[..., vis_dict[sat]]), vmin=0, vmax=1)



# img = tiff.imread(rootPath / "S2" / "post" / "ak6569814836520190622.tif")

# print(img.shape)

# for i in range(img.shape[-1]):
#     band = img[..., i]
#     lim = interval_98.get_limits(band)
#     print(f"band {i}: [{lim[0]:.2f}, {lim[1]:.2f}]")
