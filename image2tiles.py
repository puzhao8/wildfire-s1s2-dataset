""" =================> Imagery to Tiles <============== """


import os
import random
from re import split
import numpy as np
from pathlib import Path
# import solaris as sol
import tifffile as tiff
from imageio import imread, imsave
from prettyprinter import pprint

from utils.tiff2tiles import geotiff_tiling


SEED = 42
train_ratio = 0.7

random.seed(SEED)
np.random.seed(SEED)


def get_BANDS_and_BANDS_INDEX(sat, REGION, folder):
    if "S2" == sat:
        # AK
        if 'ak' == REGION:
            BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
            BANDS_INDEX = [0, 1, 2, 6, 8, 9]

        # CA
        if 'ca' == REGION:
            BANDS = ['B4', 'B8', 'B12']
            BANDS_INDEX = [0, 1, 2]

        # US
        if 'us' == REGION:
            BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
            BANDS_INDEX = [0, 1, 2, 3, 5, 6]

    if "S1" == sat:
        BANDS = ['ND', 'VH', 'VV']
        BANDS_INDEX = [0, 1, 2]

    if "ALOS" == sat:
        BANDS = ['ND', 'VH', 'VV']
        BANDS_INDEX = [0, 1, 2]

    if "mask" == sat:
        BANDS = [folder]
        BANDS_INDEX = [0]

    if "AUZ" == sat:
        if "DSM" == folder:
            BANDS = ["elevation", "slope", "aspect", "hillshade"]
            BANDS_INDEX = [0, 1, 2, 3]
        else:
            BANDS = [folder]
            BANDS_INDEX = [0]

    return BANDS, BANDS_INDEX

def tiling_wildfire_s1s2_dataset(REGION, workPath, savePath, tile_size, do_tilling=True):
    """ find events having S1, S2 and ALOS data """
    eventList = [eventName[:-4] for eventName in os.listdir(workPath / "mask" / "poly")]
    # pprint(eventList)
    # print(len(eventList))

    S2_preDir = workPath / "S2" / "pre"
    S2_postDir = workPath / "S2" / "post"


    """ S1 Selection """
    S1_preDir = workPath / "S1" / "pre"
    S1_postDir = workPath / "S1" / "post"

    def path2str(path): return str(os.path.split(path)[-1])
    event_sets = []
    for event in eventList:
        S1_preList = map(path2str, list(S1_preDir.glob(f"{event}*.tif")))
        S1_postList = map(path2str, list(S1_postDir.glob(f"{event}*.tif")))

        
        S1_intersection = list(set(S1_preList).intersection(set(S1_postList)))
        if len(S1_intersection) > 0 \
            and os.path.isfile(S2_preDir / f"{event}.tif") \
            and os.path.isfile(S2_postDir / f"{event}.tif") :
                rand = np.random.randint(0, len(S1_intersection), 1)[0]
                # print(rand, S1_intersection[rand])
                event_sets.append(S1_intersection[rand][:-4])

    pprint(event_sets)
    print(len(event_sets))
    # print(len(event_sets))

    # exit()
    """ Train & Test Split """
    split_dict = {
        'seed': SEED,
        'train_ratio': train_ratio,
        'train': {
                    'NUM': 0,
                    'ASC': 0,
                    'DSC': 0,
                    'sarname': [] 
                }, 
        'test': {
                    'NUM': 0,
                    'ASC': 0,
                    'DSC': 0,
                    'sarname': [], 
                }
            }

    # training and validation split
    train_idx = list(np.random.permutation(len(event_sets)))[:int(len(event_sets)*train_ratio)]
    print("train: ", len(train_idx))
    print(train_idx)
    for idx, sarname in enumerate(event_sets):
        print(idx, sarname)
        phase = 'train' if idx in train_idx else "test"
        # print(idx, phase)

        split_dict[phase]['sarname'].append(sarname)
        if 'ASC' in sarname: split_dict[phase]['ASC'] += 1 
        if 'DSC' in sarname: split_dict[phase]['DSC'] += 1

        if do_tilling:
            for sat in ["S2", "S1", "mask"]:
                for folder in os.listdir(workPath / sat):
                    if sat == "mask": folder = "poly"
                    dstFolder = savePath / phase / sat / folder
                    dstFolder.mkdir(parents=True, exist_ok=True)
                    
                    

                    event = ('_').join(sarname.split("_")[:-1])
                    filename = f"{sarname}.tif" if sat == "S1" else f"{event}.tif"
                    src_url = workPath / sat / folder / filename


                    BANDS, BANDS_INDEX = get_BANDS_and_BANDS_INDEX(sat, REGION, folder)

                    geotiff_tiling(sat, phase, src_url, dstFolder, BANDS, BANDS_INDEX, tile_size)


    for phase in ['train', 'test']:
        split_dict[phase]['NUM'] = len(split_dict[phase]['sarname'])

    # write to json
    import json
    with open(savePath / 'train_test_.json', 'w') as outfile:
        json.dump(split_dict,  outfile, indent=4)


if __name__ == "__main__":

    REGION = 'ca'
    YEAR = '2021'
    # 2020 all are train
    # 2021 train ratio 0.7
    workPath = Path(f"/home/v/i/vishaln/datasets/wildfire-dataset-{REGION}-{YEAR}")
    savePath = Path(f"{str(workPath)}-tiles")
 
    tiling_wildfire_s1s2_dataset(REGION, workPath, savePath, tile_size=256, do_tilling=True)
    



           