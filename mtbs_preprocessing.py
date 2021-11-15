
# Importing Libraries
import os, zipfile
from pathlib import Path 
import glob
import json

import geopandas as gpd
from shapely.geometry import Point

import matplotlib.pyplot as plt
from prettyprinter import pprint
from easydict import EasyDict as edict

from eo_class.fireEvent import FIREEVENT

import ee
ee.Initialize()
from GeoTIFF import GeoTIFF

geotiff = GeoTIFF()

def un_zip(src_url, unzipPath):
    """ unzip zip file """
    zip_file = zipfile.ZipFile(src_url)
    if os.path.isdir(unzipPath):
        pass
    else:
        os.mkdir(unzipPath)
    for names in zip_file.namelist():
        zip_file.extract(names, unzipPath)
    zip_file.close()


def load_json(url):
    with open(url, 'r') as fp:
        data = json.load(fp)
    return data

class MTBS():
    def __init__(self, cfg):
        super().__init__()

        self.workspace = cfg.workspace
        self.dataName = cfg.dataName

        self.unzipPath = self.workspace / f"{self.dataName}_UNZIP"
        self.cogPath = self.workspace / f"{self.dataName}_COG_V1"

        self.dataPath = self.workspace  / self.dataName
        self.json_url = f"outputs/{self.dataName}"


    def batch_unzip(self):
        # Loop over years
        folderList = sorted(os.listdir(self.dataPath)) # YEAR Folder
        for folder in folderList:
            print(folder)

            # Loop over zipfiles
            zipFileList = os.listdir(self.dataPath / folder)
            # pprint(zipFileList)

            for zipfilename in zipFileList:
                print(zipfilename)
                src_url = self.dataPath / folder / zipfilename
                
                unzip_event_path =  self.unzipPath / folder / zipfilename[:-4]
                if not os.path.exists(unzip_event_path): os.makedirs(unzip_event_path)

                un_zip(src_url, unzip_event_path)

    def to_cog(self, src_url, dst_url, norm_multi_sensor=False):
        if not norm_multi_sensor:
            """ Convert GeoTIFF to cloud optimized GeoTIFF """
            os.system(f"gdal_translate {src_url} {dst_url} -co TILED=YES -co COPY_SRC_OVERVIEWS=YES -co COMPRESS=LZW")

        # Special Processing for MTBS L8 Dataset
        if norm_multi_sensor:
            filename = os.path.split(src_url)[-1]
            sat = filename.split("_")[2]

            YEAR = str(src_url).split(os.sep)[-3]
            print(f"{filename}: {YEAR}")

            _, _, data = geotiff.read(src_url)
                
            if 's2' in sat.lower():
                geotiff.save(dst_url, data / 10000)

            if 'l8' in sat.lower():
                if YEAR in ['2019']:
                    geotiff.save(dst_url, data[1:7] / 1000)

                else:
                    geotiff.save(dst_url, data[:6] / 1000)

            if ('l7' in sat.lower()) or ('l5' in sat.lower()) or ('l4' in sat.lower()):
                geotiff.save(dst_url, data / 1000)
        
    def batch_convert_to_cog(self, queryKey="*nbr6.tif", norm_multi_sensor=False):
        """ Batch convert GeoTIFF to cloud optimized GeoTIFF """
        folderList = sorted(os.listdir(self.dataPath)) # YEAR Folder

        for YEAR in ["2018"]:
        # for YEAR in folderList:
            
            print(f"========> {YEAR} <=========")
            eventFolderList = os.listdir(self.unzipPath / YEAR)
            if not os.path.exists(self.cogPath / YEAR): os.makedirs(self.cogPath / YEAR)

            for event_ID in eventFolderList:
                print()
                print(f"Event_ID: {event_ID}")

                eventFolder = self.unzipPath / YEAR / event_ID

                dnbr6_list = glob.glob(str(Path(eventFolder) / "*dnbr6.tif")) # only get data when dnbr6 is available
                if len(dnbr6_list) > 0:
                    for src_url in glob.glob(str(Path(eventFolder) / queryKey)):
                        filename = os.path.split(src_url)[-1]
                        dst_url = self.cogPath / YEAR / filename

                        self.to_cog(src_url, dst_url, norm_multi_sensor=norm_multi_sensor)

    def get_roi_by_mtbs_map(self, filename):
        YEAR = filename.split("_")[0][-8:-4]
        url = f"gs://eo4wildfire/{self.dataName}_COG/{YEAR}/{filename}"
        image = ee.Image.loadGeoTIFF(url)

        # return image.geometry().bounds(ee.ErrorMargin(1))
        return image.gte(0).reduceToVectors(maxPixels=1e10, scale=30, tileScale=4, bestEffort=True).geometry()

    def save_event_dataset(self, json_url, include_roi=False):
        if json_url is None:
            json_url = self.json_url

        folderList = sorted(os.listdir(self.unzipPath)) # YEAR Folder

        EVENT_SET = edict()
        for YEAR in ["2017", "2018", "2019"]:
        # for YEAR in folderList:
            eventFolderList = os.listdir(self.unzipPath / YEAR)

            for event_id in eventFolderList:

                dnbr6_url = glob.glob(str(self.unzipPath / YEAR / event_id / "*_dnbr6.tif"))
                if len(dnbr6_url) > 0: #  if dnbr6 exists

                    mtbs_bitemporal_data = []

                    # get event info
                    print("event_id: ", event_id)
                    shp_url = glob.glob(str(self.unzipPath / YEAR / event_id / "*_burn_bndy.shp"))[0]

                    gdf = gpd.read_file(shp_url)#.to_crs(epsg=3857)

                    data = gdf.to_json()
                    event = json.loads(data)['features'][0]['properties']

                    if 'init' in gdf.crs.keys():
                        event['crs'] = gdf.crs['init'].replace("epsg", "EPSG")

                    ## TODO: get roi based on burn severity map, + biome, + modis
                    # dnbr6_url = glob.glob(str(Path(eventFolder) / "*nbr6.shp"))[0]
                    # mtbs_name = os.path.split(dnbr6_url)[-1]

                    event['name'] = event_id
                    event['YEAR'] = eval(YEAR)

                    mtbs_url = glob.glob(str(self.unzipPath / YEAR / event_id / "*nbr6.tif"))[0]
                    mtbs_bitemporal_data = sorted(glob.glob(str(self.unzipPath / YEAR / event_id / "*refl.tif")))
                    
                    # if both pre and post images are available
                    ig_date = event['Ig_Date'].replace("-", "")
                    if len(mtbs_bitemporal_data) > 1: # Bi-temporal
                        mtbs_pre_name = os.path.split(mtbs_bitemporal_data[0])[-1]
                        mtbs_post_name = os.path.split(mtbs_bitemporal_data[-1])[-1]
                        
                        print("mtbs_pre_name: ", mtbs_pre_name)
                        print("mtbs_post_name: ", mtbs_post_name)

                        if mtbs_pre_name.split("_")[1] <= ig_date:
                            event['mtbs_pre'] = mtbs_pre_name
                        else:
                            event['mtbs_pre'] = None

                        if mtbs_post_name.split("_")[1] >= ig_date:
                            event['mtbs_post'] = mtbs_post_name
                        else:
                            event['mtbs_post'] = None

                    # if there is no pre-image
                    if len(mtbs_bitemporal_data) == 1: # Single-date
                        mtbs_post_name = os.path.split(mtbs_bitemporal_data[0])[-1]
                        event['mtbs_pre'] = None
                        if mtbs_post_name.split("_")[1] >= ig_date:
                            event['mtbs_post'] = mtbs_post_name
                        else:
                            event['mtbs_post'] = None

                    # store the name of burn severity mask ended with ".dnbr6.tif"
                    event['mtbs'] = os.path.split(mtbs_url)[-1]

                    if event['mtbs_pre'] is not None:
                        pre_date = event['mtbs_pre'].split("_")[1]
                        event['pre_date'] = f"{pre_date[:4]}-{pre_date[4:6]}-{pre_date[6:8]}"

                    if event['mtbs_post'] is not None:
                        post_date = event['mtbs_post'].split("_")[1]
                        event['post_date'] = f"{post_date[:4]}-{post_date[4:6]}-{post_date[6:8]}"

                    if include_roi:
                        roi = self.get_roi_by_mtbs_map(event['mtbs'])
                        # coordinates = ee.List(roi.coordinates().get(0))
                        # rect = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()

                        event['roi'] = roi.coordinates().get(0).getInfo()
                        pprint(event)

                        # query modis burned area
                        fire = FIREEVENT(edict(event))
                        fire()
                        event.update(fire.event)

                        pprint(event)

                    EVENT_SET.update({event_id: event})

                    # save wildfire events to json
                    with open(json_url, 'w') as fp:
                        json.dump(EVENT_SET, fp, ensure_ascii=False, indent=4)

    
if __name__ == "__main__":

    KEY = 'US'
    cfg = edict({'dataName': f'MTBS_{KEY}'})
    # cfg.workspace = Path("E:/SAR4Wildfire_Dataset/Fire_Perimeters_US/MTBS/MTBS_L8_Dataset")
    cfg.workspace = Path("D:/MTBS_Landsat_Dataset")

    mtbs = MTBS(cfg)

    # # unzip
    # mtbs.batch_unzip()


    # # to cog
    # mtbs.batch_convert_to_cog(queryKey='*dnbr6.tif', norm_multi_sensor=False)
    mtbs.batch_convert_to_cog(queryKey='*refl.tif', norm_multi_sensor=True)  

    # save events as geojson
    mtbs.save_event_dataset(json_url=f"outputs/MTBS_{KEY}_2017_2019_events_woROI.json", include_roi=False)

    
    """ if include roi, you need to upload dnbr6 cog to cloud. """
    # upload to cloud
    if False:
        KEY = "US"
        local_dir = f"D:/MTBS_Landsat_Dataset/MTBS_{KEY}_ZIP_COG"
        for YEAR in os.listdir(Path(local_dir)):
            print(f"gsutil -m cp -r {local_dir}/{YEAR}/*nbr6.tif gs://eo4wildfire/MTBS_{KEY}_COG/{YEAR}")
            os.system(f"gsutil -m cp -r {local_dir}/{YEAR}/*nbr6.tif gs://eo4wildfire/MTBS_{KEY}_COG/{YEAR}")

      
    # save events as geojson
    # mtbs.save_event_dataset(json_url=f"outputs/MTBS_{KEY}_2010_2016_events_ROI.json", include_roi=False)
    
    

