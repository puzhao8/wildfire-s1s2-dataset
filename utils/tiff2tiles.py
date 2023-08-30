import os
import numpy as np
# from utils.GeoTIFF import GeoTIFF
from pathlib import Path
import tifffile as tiff
import matplotlib.pyplot as plt
from PIL import Image

def normalize_sar(img):
    return (np.clip(img, -30, 0) + 30) / 30


# geotiff = GeoTIFF()
def geotiff_tiling(sat, phase, src_url, dst_dir, BANDS, BANDS_INDEX, tile_size=256, tiling=True):
    
    '''
    modified the code to instead save as png files. Hence the preprocessing is also done for S1 and S2 images.
    '''
    if sat not in ["mask", "S2"]:
        sarname = os.path.split(src_url)[-1][:-4]
        orbKey = sarname.split("_")[-1]
        event_id = sarname[:(-len(orbKey)-1)]
    else:
        sarname = os.path.split(src_url)[-1][:-4]
        orbKey = "mask"
        event_id = sarname

    print(f"SAR: {sarname}")
    print(f"Orbit: {orbKey}")
    print(f"src_url: {src_url}")
    
    print(f"{event_id}: tiling")
    print(f"Bands: {BANDS}")
    print(f"Phase: {phase}")
    print("Satellite: ", sat)
    # _, _, im_data = geotiff.read(src_url)
    # reading the image using tifffile
    im_data = tiff.imread(src_url)
    im_data = np.nan_to_num(im_data, 0)

    # if sat == "S1":
    #     im_data = normalize_sar(im_data)
    if sat == "mask":
        im_data = im_data[..., np.newaxis]
    else:
        im_data = im_data[..., BANDS_INDEX]


    if 'test' == phase: 
        test_img_dir = Path(str(dst_dir).replace('test', 'test'))
        
        # if len(im_data.shape)==2: 
        # image = Image.fromarray((im_data*255).astype(np.uint8))
        # image.save(test_img_dir / f"{event_id}.png")
            # plt.imsave(test_img_dir / f"{event_id}.png", im_data, cmap='gray')
        # geotiff.save(
        #         url= test_img_dir / f"{event_id}.tif", 
        #         im_data=im_data, 
        #         bandNameList=BANDS
        #     )
        # else:
        #     plt.imsave(test_img_dir / f"{event_id}.png", im_data)
        # print(f"Saved {test_img_dir / f'{event_id}.png'}")
    # print(im_data.dtype.name)
    # print(im_data.shape)
    # print(im_data.min(), im_data.max())
    if tiling:
        im_data = im_data.transpose(2, 0, 1)
        C, H, W = im_data.shape
        # print(C, H, W)

        H_ = (H // tile_size + 1) * tile_size - H
        W_ = (W // tile_size + 1) * tile_size - W

        # print(H_, W_)
        # select bands
        bottom_pad = np.flip(im_data[:, H-H_:H, :], axis=1)
        # print(bottom_pad.shape)

        # dim2
        im_data_expanded = np.hstack((im_data, bottom_pad))
        right_pad = np.flip(im_data_expanded[:, :, W-W_:W], axis=2)

        # dim3
        im_data_expanded = np.dstack((im_data_expanded, right_pad))
        # print(im_data_expanded.shape)

        print(im_data_expanded.shape)
        _, H1, W1 = im_data_expanded.shape
        
        for i in range(0, H1 // tile_size):
            for j in range(0, W1 // tile_size):
                tile = im_data_expanded[:, i*256:(i+1)*256, j*256:(j+1)*256]
                # geotiff.save(
                #     url=dst_dir / f"{event_id}_{i}_{j}.png", 
                #     im_data=tile, 
                #     bandNameList=BANDS,
                #     tiling=tiling
                # )
                # tile = np.squeeze(tile.transpose(1, 2, 0))
                tiff.imwrite(dst_dir / f"{event_id}_{i}_{j}.tif", tile)
                print('writing tile: ', str(dst_dir / f"{event_id}_{i}_{j}.tif"))
                # image = Image.fromarray((tile*255).astype(np.uint8))
                # image.save(dst_dir / f"{event_id}_{i}_{j}.png")
                # print('writing tile: ', str(dst_dir / f"{event_id}_{i}_{j}.png"))
                # exit()

        # exit()
    # if sat == "mask":
    #     exit()

if __name__ == "__main__":

    BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
    BANDS_INDEX = [0, 1, 2, 6, 8, 9]

    src_url = "D:\wildfire-s1s2-dataset-ak\S2\post/ak6186714639320190717.tif"
    dst_dir = Path("G:\PyProjects\smp-seg-pytorch\outputs")

    geotiff_tiling(src_url, dst_dir, BANDS, BANDS_INDEX, tile_size=256)