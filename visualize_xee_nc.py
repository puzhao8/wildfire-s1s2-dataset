#%% read .nc file with tables
import matplotlib.pyplot as plt
import tables
import numpy as np
from astropy.visualization import PercentileInterval
norm = PercentileInterval(95)

import warnings
warnings.filterwarnings("ignore")

# CA_2019_NT_8, CA_2019_AB_172
filename = "CA_2019_NT_8"
ds = tables.open_file(f'outputs\wildfire-s1s2-dataset-ca-V2\{filename}.h5')



bandDict = {
    'S2': ['B4', 'B8', 'B12'],
    'S1': ['VH', 'VV'],
    'AL': ['HV', 'HH'],
}

images = []

LC = np.array(ds.root['AUZ/landcover/landcover']).transpose(0,2,1)[0,]
waterMask = (LC!=80).astype(float)

# Sentinel-2
def nbr(stage='post'): 
    B8 = norm(np.array(ds.root[f"S2/{stage}/B8"]).transpose(0,2,1)[0,])
    B12 = norm(np.array(ds.root[f"S2/{stage}/B12"]).transpose(0,2,1)[0,])
    return (B8 - B12) / (B8 + B12)

S2_post = np.vstack((ds.root['S2/post/B12'], ds.root['S2/post/B8'], ds.root['S2/post/B4'])).transpose(2,1,0)
S2_pre = np.vstack((ds.root['S2/pre/B12'], ds.root['S2/pre/B8'], ds.root['S2/pre/B4'])).transpose(2,1,0)
NBR_post = np.nan_to_num(nbr('post'))
dNBR = np.nan_to_num(nbr('pre')) - NBR_post
images = images + [(norm(S2_pre), 'S2/pre'), 
                   (norm(S2_post), 'S2/post'), 
                   (norm(NBR_post * waterMask), 'S2/post/NBR'), 
                   (norm(dNBR * waterMask), 'S2/dNBR')]

# AUZ
# LC = np.array(ds.root['AUZ/landcover/landcover']).transpose(0,2,1)[0,]
# waterMask = (LC!=80).astype(float)
DEM = np.array(ds.root['AUZ/DEM/elevation']).transpose(0,2,1)[0,]
slope = np.array(ds.root['AUZ/DEM/slope']).transpose(0,2,1)[0,]
images = images + [(LC, 'LandCover'), (DEM, 'DEM')]

# SAR
for sat in ['S1', 'AL']:
    bandList = bandDict[sat]
    for band in bandList:
        pre = norm(np.array(ds.root[f"{sat}/pre/{band}"]).transpose(0,2,1)[0,])
        post = norm(np.array(ds.root[f"{sat}/post/{band}"]).transpose(0,2,1)[0,])
        logRt = norm(pre - post)
        images = images + [(pre, f"{sat}/pre/{band}"), 
                           (post, f"{sat}/post/{band}"), 
                           (logRt, f"{sat}/logRt/{band}")]


#%%
nRows, nCols = 3, 6
plt.figure()
fig, ax = plt.subplots(nRows, nCols)

cnt = 0
for i in range(nRows):
    for j in range(nCols):
        arr, subtitle = images[cnt][0], images[cnt][-1]
        if cnt < 2: ax[i,j].imshow(arr)
        else: ax[i,j].imshow(arr, cmap='gray')
        cnt += 1
        ax[i,j].set_title(subtitle, fontdict={'fontsize': 8})
        ax[i,j].set_xticks([])
        ax[i,j].set_yticks([])   

# plt.show()   
fig.tight_layout()
fig.savefig(f"outputs/wildfire-s1s2-dataset-ca-V2/{filename}.png", dpi=200) 