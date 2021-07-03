
import os
import numpy as np
from imageio import imread, imsave
import matplotlib.pyplot as plt
import tifffile as tiff
from pathlib import Path
from astropy.visualization import PercentileInterval
interval_98 = PercentileInterval(98)

bucket = "wildfire-s1s2-dataset-ca"
rootPath = Path(f"D:\{bucket}")
vis_dict = {
    'ALOS': [0, 1, 2],
    'S1': [0, 1, 2],
    'S2': [9, 6, 2], # B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12, cloud
    'mask': 0,
    'AUZ': 0
}

sat = os.listdir(rootPath)
for sat in vis_dict.keys():
    for stage in os.listdir(rootPath / sat):
        for filename in os.listdir(rootPath / sat / stage):

            save_dir = Path("D:/") / f"{bucket}-check" / sat / stage
            if not os.path.exists(save_dir): os.makedirs(save_dir)
            dst_url =  save_dir / f"{filename[:-4]}.png"
            print(dst_url)
            
            image = tiff.imread(rootPath / sat / stage / filename)
            image = np.nan_to_num(image, -30)
            print(image.shape)

            if sat in ['mask', 'AUZ']: plt.imsave(dst_url, interval_98(image), vmin=0, vmax=1)
            else: plt.imsave(dst_url, interval_98(image[..., vis_dict[sat]]), vmin=0, vmax=1)



# for sat in ['mask', 'AUZ']:


# img = tiff.imread(rootPath / "S2" / "post" / "ak6569814836520190622.tif")

# print(img.shape)

# for i in range(img.shape[-1]):
#     band = img[..., i]
#     lim = interval_98.get_limits(band)
#     print(f"band {i}: [{lim[0]:.2f}, {lim[1]:.2f}]")
