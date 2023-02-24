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



def save_fireEvents_to_json(EVENT_SET, save_url):
    ## """ Save Dict to YAML and READ """

    # save wildfire events to json
    with open(f"{save_url}.json", 'w') as fp:
        json.dump(EVENT_SET, fp, ensure_ascii=False, indent=4)

def set_property(feat):
        return feat.set("NAME", ee.String(feat.get("AGENCY")).cat("_")\
                .cat(ee.Number(feat.get("NFIREID")).toInt().format()))
                # .set("polyStartDate", ee.Date(feat.get("SDATE")).format().slice(0, 10))\
                # .set('polyEndDate', ee.Date(feat.get("EDATE")).format().slice(0, 10))

def get_local_crs_by_query_S2(roi):
        # return ee.ImageCollection("COPERNICUS/S2")\
        #             .filterDate("2020-05-01", "2021-01-01")\
        #             .filterBounds(roi.centroid(ee.ErrorMargin(20))).first()\
        #             .select(0).projection().crs().getInfo()

        return "EPSG:32610"

class FIREEVENT:
    def __init__(self, cfg):
        # super().__init__(cfg)

        self.cfg = cfg
        self.cfg.saveName = f"POLY_{cfg.COUNTRY}_{cfg.YEAR}_events_gt2k"
        self.save_url = f"./wildfire_events/{self.cfg.saveName}"

        ## Canada Wildfire Polygons 
        # BC_FirePerimeter = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/BC_Historical_Fire_Polygon_before2020").map(setYear)     

        CA_2017 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2017_r9_20190919")
        CA_2018 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2018_r9_20200703")
        CA_2019 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2019_r9_20200703")  
        self.CA_BurnAreaPolys = CA_2017.merge(CA_2018).merge(CA_2019)

        # CA_2019 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2019_r9_20200703")  
        # self.CA_BurnAreaPolys = CA_2019

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
        polyFiltered = (self.CA_BurnAreaPolys
                            .filter(ee.Filter.eq("YEAR", self.cfg.YEAR))
                            .filter(ee.Filter.gt("ADJ_HA", self.cfg.ADJ_HA_TH))\
                            # .filter(ee.Filter.lte("ADJ_HA", self.cfg.ADJ_HA_TH))
                            .map(set_property)
        )

        # firename list
        nameList = polyFiltered.aggregate_array("NAME").getInfo()

        print("\n\n---------------------> logs <---------------------")
        print(f"There are {polyFiltered.size().getInfo()} wildfire events (>{int(self.cfg.ADJ_HA_TH)} ha) in {self.cfg.YEAR}.")

        # for idx in range(0, 2): #polyFiltered.size().getInfo()):
        for name in nameList:
            
            poly = polyFiltered.filter(ee.Filter.eq("NAME", name)).first()
            burned_area = poly.get("ADJ_HA").getInfo()
            
            # poly = ee.Feature(polyList.get(idx))
            # polyMap = poly.style(color='white', fillColor='white', width=0) \
            #         .select('vis-red').gt(0).rename('poly')


            # get bottom-left and top-right points
            roi = poly.geometry().bounds()       
            crs = get_local_crs_by_query_S2(roi)
            # crs = "EPSG:4326"

            # rect = roi.coordinates().get(0).getInfo()

            coordinates = ee.List(roi.coordinates().get(0)).serialize()
            print(coordinates)

            rect = [coordinates[0], coordinates[2]]
            print("rect: ", rect)

            event = edict(poly.toDictionary().getInfo())
            eventName = f"CA_{event.YEAR}_{event.NAME}".replace("-","")

            print(f"{eventName}: {burned_area}")
            print(f"CRS: {crs}")

            event.update({
                'NAME': eventName,
                'roi': rect,
                'year': event.YEAR,
                'crs': crs,
                'modis_min_area': self.cfg.modis_min_area,
            })

            # convert property (in number) into Date
            for property in ["AFSDATE", "AFEDATE", "SDATE", "EDATE", "CAPDATE"]:
                value = poly.get(property).getInfo()
                if value is not None:
                    event[property] = ee.Date(poly.get(property)).format().slice(0,10).getInfo() 
                else:
                    event[property] = None

            # Obtain Burn Period from MODIS Burned Area Products
            modis = MODIS_POLY(event)
            modis()

            event.update({'roi': rect})
            
            # Use MODIS BurnDate to correct fireStartDate and fireEndDate
            event.modisStartDate = modis.unionPoly.startDate 
            event.modisEndDate = modis.unionPoly.endDate 

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
        polyFiltered = (self.CA_BurnAreaPolys
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