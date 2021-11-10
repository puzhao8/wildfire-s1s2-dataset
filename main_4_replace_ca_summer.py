
import os 
from pathlib import Path
import shutil

S2_tif_folder = Path("D:\wildfire-s1s2-dataset-ca-summer\S2")
S2_replace_folder = Path("D:\wildfire-s1s2-dataset-ca-summer-check\S2-summer-replace")
S2_replace_tif_folder = Path("D:\wildfire-s1s2-dataset-ca-summer-check\S2-summer-replace-tif")
S2_replace_tif_folder.mkdir(exist_ok=True)

for folder in os.listdir(S2_replace_folder):
    for filename in os.listdir(S2_replace_folder / folder):
        tifname = filename.replace(".png", ".tif")
        src_url = S2_tif_folder / folder / tifname

        saveFolder = S2_replace_tif_folder / folder
        saveFolder.mkdir(exist_ok=True)
        # dst_url =  saveFolder / tifname
        print(saveFolder)

        shutil.copy(src_url, saveFolder)

        