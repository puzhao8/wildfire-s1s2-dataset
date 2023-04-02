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

def get_burn_peroid_from_monthly_burned_area(year=2017, roi=None):
    ''' derive burn period from MODIS monthly burned area product '''
    roi = ee.Geometry.Rectangle(roi)

    yearFirstDay = ee.Date(ee.Number(year).format().cat("-01-01"))
    yearEndDay = ee.Date(ee.Number(year).add(1).format().cat("-01-01"))
    modis_imgCol = ee.ImageCollection("MODIS/006/MCD64A1").filterDate(yearFirstDay, yearEndDay)

    modisYearlyMosaic = modis_imgCol.mosaic().select('BurnDate')
    burn_period = modisYearlyMosaic.reduceRegion(
          reducer = ee.Reducer.minMax(),
          geometry = roi,
          scale = 500,
          maxPixels = 1e20,
    )

    julian_start = burn_period.get('BurnDate_min')
    julian_end = burn_period.get('BurnDate_max')
    modisStartDate = yearFirstDay.advance(ee.Number(julian_start).subtract(1), 'day').format().slice(0,10)
    modisEndDate = yearFirstDay.advance(ee.Number(julian_end).subtract(1), 'day').format().slice(0,10)

    return {
        'julian_start': julian_start.getInfo(),
        'julian_end': julian_end.getInfo(),
        'modisStartDate': modisStartDate.getInfo(),
        'modisEndDate': modisEndDate.getInfo(),
    }


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
    ''' write a dictionary object into a json file specified by the second parameter '''
    with open(json_url, 'w') as fp:
        json.dump(edict(event), fp, ensure_ascii=False, indent=4)

# save wildfire events to json
def load_json(url) -> edict:
    ''' read a json file and convert'''
    with open(url, 'r') as fp:
        data = edict(json.load(fp))
    return data

class FIREEVENT:
    """
    This class is designed to query BIOME and MODIS Burned Area Products (500m) 
    by a specified name, ROI, and YEAR.
    """

    def __init__(self, 
            country= 'EU',
            event_name = None,
            event_year = 2017,
            roi = None,
            buffer_size = 1e4,
            min_burned_area = 2e3, # 2e4, burned areas
            modis_min_area = 1e2, # ignore small polygons for modis, 1e4
            save_flag = True,
            save_url = f"wildfire_events/fire_events_exported.json", 
            **kwargs
        ):
        
        self.country = country
        self.min_burned_area = min_burned_area
        self.modis_min_area = modis_min_area
        self.buffer_size = buffer_size
        self.save_url = save_url
        self.save_flag = save_flag
        self.event_name = event_name
        self.event_year = event_year
        self.roi = roi


    def get_biome(self, roi):
        biomeImg, eco_names = self.query_biome_climate_zone()
        BIOME_NUM = biomeImg.reduceRegion(ee.Reducer.mode(), roi, 500).getInfo()['BIOME_NUM']
        BIOME_NAME = eco_names.getInfo()[BIOME_NUM]
        return BIOME_NUM, BIOME_NAME

    def query_biome_climate_zone(self):
        """ query biome data. """

        ### Climate Zone ###
        ecoRegions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
        eco_palette = ecoRegions.aggregate_array("COLOR_BIO").distinct()
        eco_names = ecoRegions.aggregate_array("BIOME_NAME").distinct()

        biomeRegions = ecoRegions.setMulti({
            'palette': eco_palette,
            'names': eco_names 
        })

        biomeImg = ee.FeatureCollection(biomeRegions).reduceToImage(['BIOME_NUM'], ee.Reducer.first()).rename("BIOME_NUM")
        return biomeImg, eco_names

    def query_modis_fireEvent_info(self):
        """ query modis progression data to derive fireStartDate and fireEndDate. """

        event = edict()

        # get bottom-left and top-right points
        roi = ee.Geometry.Rectangle(self.roi)
        if self.buffer_size > 0:
            roi = roi.buffer(self.buffer_size).bounds()
            
        crs = get_local_crs_by_query_S2(roi)

        coordinates = ee.List(roi.coordinates().get(0))
        rect = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()
        
        print(f"event name: {self.event_name}")
        print(f"CRS: {crs}")

        biome_num, biome_name = self.get_biome(roi)

        event.update({
            'name': self.event_name,
            'roi': rect,
            'year': self.event_year, # modified from self.cfg.year
            'crs': crs,

            'BIOME_NUM': biome_num,
            'BIOME_NAME': biome_name,

            'modis_min_area': self.modis_min_area
        })

        # Obtain Burn Period from MODIS Burned Area Products
        # modis = MODIS_POLY(event)
        # modis()

        burn_period = get_burn_peroid_from_monthly_burned_area(event.year, event.roi)
        
        event.update(burn_period)
        event.update({'roi': rect})
        
        # # Use MODIS BurnDate to correct fireStartDate and fireEndDate
        # event.modisStartDate = modis.unionPoly.startDate 
        # event.modisEndDate = modis.unionPoly.endDate 

        if self.save_flag: save_fireEvent_to_json(event, self.save_url)


if __name__=="__main__":

    cfg = edict(
            country= 'EU',
            event_name = 'BC2017C10784',
            event_year = 2017,
            roi = [-124.52783481782407, 52.26491528311718, -122.73599679662699, 53.35226349843808],

            min_burned_area = 2e3, # 2e4, burned areas
            modis_min_area = 1e2, # ignore small polygons for modis, 1e4
            buffer_size = 1e4,
            poly_min_area = 1e3, # ignore small polygons in modis, 1e4,

            # 'name': 'BC2017C10784',
            # 'YEAR': 2017,
            # 'roi': [-124.52783481782407, 52.26491528311718, -122.73599679662699, 53.35226349843808],
        )

    fireEvent = FIREEVENT(**cfg)
    fireEvent.query_modis_fireEvent_info(
        save_flag = True,
        save_url = f"wildfire_events/fire_events_exported.json", )

    # your_fire = fireEvent.event
    # pprint(your_fire)