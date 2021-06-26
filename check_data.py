

import tifffile as tiff
from pathlib import Path
from astropy.visualization import PercentileInterval
interval_98 = PercentileInterval(98)

rootPath = Path("D:\wildfire-s1s2-dataset")
img = tiff.imread(rootPath / "S2" / "post" / "ak6569814836520190622.tif")

print(img.shape)

for i in range(img.shape[-1]):
    band = img[..., i]
    lim = interval_98.get_limits(band)
    print(f"band {i}: [{lim[0]:.2f}, {lim[1]:.2f}]")
