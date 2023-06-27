import ee
from pyasn1.type.univ import Null
ee.Initialize()

from easydict import EasyDict as edict
from prettyprinter import pprint

import logging
logger = logging.getLogger(__name__)

from eo_class.modisPoly import MODIS_POLY
from easydict import EasyDict as edict
import yaml, json
import numpy as np

import os
os.environ["PYDEVD_WARN_EVALUATION_TIMEOUT"] = "1e5"
os.environ["PYDEVD_THREAD_DUMP_ON_WARN_EVALUATION_TIMEOUT"] = "True"

from eo_class.modisPoly import get_first_cloud_free_modis

def save_fireEvents_to_json(EVENT_SET, save_url):
    ## """ Save Dict to YAML and READ """

    # save wildfire events to json
    with open(f"{save_url}.json", 'w') as fp:
        json.dump(EVENT_SET, fp, ensure_ascii=False, indent=4)

def set_property(feat):
    YEAR = ee.String(feat.get('Event_ID')).slice(-8,-4).getInfo()
    return feat.set("NAME", ee.String(f"US_{YEAR}_").cat(feat.get('Event_ID')))
        # # Canada
        # feat.set("NAME", ee.String(feat.get("AGENCY")).cat("_")\
        #     .cat(ee.Number(feat.get("NFIREID")).toInt().format()))
        #     .set("polyStartDate", ee.Date(feat.get("SDATE")).format().slice(0, 10))\
        #     .set('polyEndDate', ee.Date(feat.get("EDATE")).format().slice(0, 10))


def get_local_crs_by_query_S2(roi):
    return ee.ImageCollection("COPERNICUS/S2")\
                .filterDate("2020-05-01", "2021-01-01")\
                .filterBounds(roi.centroid(ee.ErrorMargin(20))).first()\
                .select(0).projection().crs().getInfo()

class FIREEVENT:
    def __init__(self, cfg):
        # super().__init__(cfg)

        self.cfg = cfg
        self.cfg.saveName = f"MTBS_{cfg.COUNTRY}_{cfg.YEAR}_events"
        self.save_url = f"./wildfire_events/{self.cfg.saveName}"

        # MTBS 
        # self.BurnAreaPolys = ee.FeatureCollection("users/omegazhangpzh/C_US_Fire_Perimeters/MTBS_Perimeter_1984_2021")
        self.BurnAreaPolys = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")


    def __call__(self):
        self.query_biome_climate_zone()
        self.query_wildfire_events_info()

        # self.save_fireEvents_to_yaml(save_url)
        # self.save_fireEvents_to_json(save_url)


    def get_biome(self, roi):
        return self.biomeImg.reduceRegion(ee.Reducer.mode(), roi, 500).getInfo()['BIOME_NUM']

    def query_biome_climate_zone(self):
        ### Climate Zone ###
        ecoRegions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
        self.eco_palette = ecoRegions.aggregate_array("COLOR_BIO").distinct()
        self.eco_names = ecoRegions.aggregate_array("BIOME_NAME").distinct()

        biomeRegions = ecoRegions.setMulti({
            'palette': self.eco_palette,
            'names': self.eco_names 
        })

        self.biomeImg = ee.FeatureCollection(biomeRegions).reduceToImage(['BIOME_NUM'], ee.Reducer.first()).rename("BIOME_NUM")

    def query_wildfire_events_info(self):
        # areaTH = 1e4 # ignore small polygons
        # YEAR = 2017
        # ADJ_HA = 10e4
        # bufferSize = 0

        self.EVENT_SET = edict()
        year_filter = ee.Filter.And(ee.Filter.gte("Ig_Date", ee.Date(f"{self.cfg.YEAR}-01-01").millis()),
                                    ee.Filter.lte("Ig_Date", ee.Date(f"{self.cfg.YEAR}-12-31").millis()))
        polyFiltered = (self.BurnAreaPolys
                            .filter(year_filter)
                            .filter(ee.Filter.gt("BurnBndAc", self.cfg.ADJ_HA_TH * 2.471))\
                            # .filter(ee.Filter.lte("ADJ_HA", self.cfg.ADJ_HA_TH))
                            # .map(set_property)
        )

        # polyFiltered = polyFilteredV0.map(set_property)

        # firename list
        nameList = polyFiltered.aggregate_array("Event_ID").getInfo()

        print("\n\n---------------------> logs <---------------------")
        print(f"There are {polyFiltered.size().getInfo()} wildfire events (>{int(self.cfg.ADJ_HA_TH)} ha) in {self.cfg.YEAR}.")

        # for idx in range(0, 2): #polyFiltered.size().getInfo()):
        for event_id in nameList:
            year = event_id[-8:-4]
            poly = polyFiltered.filter(ee.Filter.eq("Event_ID", event_id))
            
            # get bottom-left and top-right points
            roi = poly.union(ee.ErrorMargin(100)).geometry().bounds()       
            crs = get_local_crs_by_query_S2(roi)

            coordinates = roi.coordinates().get(0).getInfo()
            rect = [coordinates[0], coordinates[2]]
            print("rect: ", rect)

            event = edict(poly.first().toDictionary().getInfo())
            eventName = f"US_{year}_{event_id}"

            print(f"{eventName}")
            print(f"CRS: {crs}")

            event.update({
                'NAME': eventName,
                'roi': rect,
                'year': int(year),
                'crs': crs,
                'modis_min_area': self.cfg.modis_min_area,
            })


            # Obtain Burn Period from MODIS Burned Area Products
            modis = MODIS_POLY(event)
            modis()

            event.update({'roi': rect})
            
            # Use MODIS BurnDate to correct fireStartDate and fireEndDate
            event.modisStartDate = modis.unionPoly.startDate 
            event.modisEndDate = modis.unionPoly.endDate 

            # add the date when the first cloud-free modis image was acquried after fire
            temp_date = event.Post_ID[-8:]
            landsat_post_date = f"{temp_date[-8:-4]}-{temp_date[-4:-2]}-{temp_date[-2:]}"
            end_date = event['modisEndDate'] or landsat_post_date or ee.Date(event.YEAR).advance(9, 'month')
            modis_cloud_free_date = get_first_cloud_free_modis(roi, end_date)
            event.modis_cloud_free_date = modis_cloud_free_date

            # Get BIOME info. 
            event.BIOME_NUM = self.get_biome(roi)
            event.BIOME_NAME = self.eco_names.getInfo()[int(event.BIOME_NUM)]

            self.EVENT_SET.update({eventName: event})

            save_fireEvents_to_json(self.EVENT_SET, self.save_url)

    def define_event_by_poly(self, poly):
        # polyMap = poly.style(color='white', fillColor='white', width=0) \
        #             .select('vis-red').gt(0).rename('poly')

        # get bottom-left and top-right points
        roi = ee.Feature(poly).bounds().geometry()
        # crs = get_local_crs_by_query_S2(roi)

        coordinates = ee.List(roi.coordinates().get(0))
        rect = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()

        event = edict(poly.toDictionary().getInfo())
        eventName = f'CA_{event.YEAR}_{event.NAME}'

        # print(f"{idx}: {eventName}")
        # print(f"CRS: {crs}")

        event.update({
            'roi': rect,
            'year': event.YEAR,
            # 'crs': crs,
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
        event.BIOME_NUM = self.get_biome(roi)
        event.BIOME_NAME = self.eco_names.getInfo()[event.BIOME_NUM]

        event.eventName = eventName
        return event

    def query_wildfire_events_info_v2(self):
        # areaTH = 1e4 # ignore small polygons
        # YEAR = 2017
        # ADJ_HA = 10e4
        # bufferSize = 0

        self.EVENT_SET = edict()
        polyFiltered = (self.BurnAreaPolys
                            .filter(ee.Filter.eq("YEAR", self.cfg.YEAR))
                            .filter(ee.Filter.gt("ADJ_HA", self.cfg.ADJ_HA_TH))\
                            # .filter(ee.Filter.lte("ADJ_HA", self.cfg.ADJ_HA_TH))
                            .map(set_property)
        )

        polyList = polyFiltered.toList(polyFiltered.size())

        print("\n\n---------------------> logs <---------------------")
        print(f"There are {polyFiltered.size().getInfo()} wildfire events (>{int(self.cfg.ADJ_HA_TH)} ha) in {self.cfg.YEAR}.")

        # eventList = []
        # def myAlg(poly, first):
        #     event = self.define_event_by_poly(poly)
        #     return list(first).append(event)
        # eventList = polyFiltered.iterate(myAlg, eventList)

        for idx in range(0, polyFiltered.size().getInfo()):
            # poly = polyFiltered.first()
            poly = ee.FeatureCollection(polyList.get(idx))
            event = self.define_event_by_poly(poly)

            print(f"{idx}: {event.eventName}")
            self.EVENT_SET.update({event.eventName: event})

        # for idx in range(0, polyFiltered.size().getInfo()):
        #     # poly = polyFiltered.first()
        #     poly = ee.FeatureCollection(polyList.get(idx))
        #     event = self.define_event_by_poly(poly)
        #     self.EVENT_SET.update({event.eventName: event})


    def save_fireEvents_to_yaml(self, save_url):
        ## """ Save Dict to YAML and READ """
        with open(f"{save_url}.yaml", 'wt') as ymlfile:
            yaml.dump(self.EVENT_SET, ymlfile)

    def load_fireEvents_yaml(self, yml_url):
        with open(yml_url, 'rt') as ymlfile:
            self.EVENT_SET = yaml.load(ymlfile)




if __name__=="__main__":

    cfg = edict({
        'COUNTRY': 'Canada',
        # 'YEAR': 2017,
        'ADJ_HA_TH': 1e3, # 2e4
        'MIN_HA_TH': 1e2, # ignore small polygons, 1e4
        # 'bufferSize': 0,
        # 'yml_url': 'CA_2017_Wildfire_V1.yaml'
    })

    for YEAR in range(2018, 2021):
        cfg.YEAR = YEAR

        fireEvents = FIREEVENT(cfg)
        fireEvents()