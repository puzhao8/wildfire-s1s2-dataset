from typing import Dict
import ee
ee.Initialize()

from easydict import EasyDict as edict
from prettyprinter import pprint

import logging
logger = logging.getLogger(__name__)

from eo_class.modisPoly import MODIS_POLY
import yaml
import numpy as np
import json

def set_property(feat):
        return feat.set("NAME", ee.String(feat.get("AGENCY")).cat(ee.Number(feat.get("NFIREID")).toInt().format()))\
                # .set("polyStartDate", ee.Date(feat.get("SDATE")).format().slice(0, 10))\
                # .set('polyEndDate', ee.Date(feat.get("EDATE")).format().slice(0, 10))

def get_local_crs_by_query_S2(roi):
        return ee.ImageCollection("COPERNICUS/S2")\
                    .filterDate("2018-01-01", "2019-01-01")\
                    .filterBounds(roi.centroid(ee.ErrorMargin(1))).first()\
                    .select(0).projection().crs().getInfo()


# save wildfire events to json
def save_fireEvent_to_json(event: edict, json_url: str) -> None:
    with open(json_url, 'w') as fp:
        json.dump(edict(event), fp, ensure_ascii=False, indent=4)

# save wildfire events to json
def load_json(url) -> edict:
    with open(url, 'r') as fp:
        data = edict(json.load(fp))
    return data

class FIREEVENT:
    """
    This class is designed to query BIOME and MODIS Burned Area Products (500m) 
    by a specified name, ROI, and YEAR.
    """

    def __init__(self, cfg):
        # super().__init__(cfg)
        self.cfg = cfg
        self.cfg['MIN_HA_TH'] = 1e3 # ignore small polygons in modis, 1e4

    def __call__(self):
        """ query biome -> query modis -> save derived fireEvent. """

        self.query_biome_climate_zone()
        event = self.query_modis_fireEvent_info()
        # self.save_fireEvents_set()

        save_fireEvent_to_json(event, f"wildfire_events/{self.cfg.name}.json")


    def get_biome(self, roi):
        return self.biomeImg.reduceRegion(ee.Reducer.mode(), roi, 500).getInfo()['BIOME_NUM']

    def query_biome_climate_zone(self):
        """ query biome data. """

        ### Climate Zone ###
        ecoRegions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
        self.eco_palette = ecoRegions.aggregate_array("COLOR_BIO").distinct()
        self.eco_names = ecoRegions.aggregate_array("BIOME_NAME").distinct()

        biomeRegions = ecoRegions.setMulti({
            'palette': self.eco_palette,
            'names': self.eco_names 
        })

        self.biomeImg = ee.FeatureCollection(biomeRegions).reduceToImage(['BIOME_NUM'], ee.Reducer.first()).rename("BIOME_NUM")

    def query_modis_fireEvent_info(self):
        """ query modis progression data to derive fireStartDate and fireEndDate. """

        event = edict()

        # get bottom-left and top-right points
        roi = ee.Geometry.Rectangle(list(self.cfg.roi))
        crs = get_local_crs_by_query_S2(roi)

        coordinates = ee.List(roi.coordinates().get(0))
        rect = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()
        
        print(f"{self.cfg.name}")
        print(f"CRS: {crs}")

        event.update({
            'name': self.cfg.name,
            'roi': rect,
            'year': self.cfg.YEAR,
            'crs': crs,
            'areaTH': self.cfg.MIN_HA_TH,
        })

        # Obtain Burn Period from MODIS Burned Area Products
        modis = MODIS_POLY(event)
        modis()

        event.update({'roi': rect})
        
        # Use MODIS BurnDate to correct fireStartDate and fireEndDate
        event.modisStartDate = modis.unionPoly.startDate 
        event.modisEndDate = modis.unionPoly.endDate 

        # Get BIOME info. 
        event.BIOME_NUM = int(self.get_biome(roi))
        event.BIOME_NAME = self.eco_names.getInfo()[event.BIOME_NUM]
        
        self.event = event
        return event


    def save_fireEvent_to_yaml(self, yaml_url):
        ## """ Save Dict to YAML and READ """

        # yml_url = f"outputs/{self.cfg.name}.yaml"
        with open(yaml_url, 'wt') as ymlfile:
            yaml.dump(self.event, ymlfile) # deafult_flow_style=False

    def load_fireEvents_yaml(self, yml_url):
        with open(yml_url, 'rt') as ymlfile:
            self.EVENT_SET = yaml.load(ymlfile) # Loader=yaml.UnsafeLoader




if __name__=="__main__":

    cfg = edict({
        'name': 'BC2017C10784',
        'YEAR': 2017,
        'roi': [-124.52783481782407, 52.26491528311718, -122.73599679662699, 53.35226349843808],
    })

    fireEvent = FIREEVENT(cfg)
    fireEvent()

    your_fire = fireEvent.event
    pprint(your_fire)