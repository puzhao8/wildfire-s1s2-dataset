
from typing import Dict
import ee
ee.Initialize()

from easydict import EasyDict as edict
from prettyprinter import pprint

import logging
logger = logging.getLogger(__name__)

# from eo_class.modisPoly import MODIS_POLY
import yaml
import numpy as np
import json

""" CFG """
cfg = edict({
    "JSON": "G:\PyProjects\wildfire-s1s2-dataset\wildfire_events\MTBS_AK_2017_2019_events_ROI.json"
})


""" #################################################################
Wildfire Event
################################################################# """ 
from eo_class.fireEvent import load_json
print(cfg.JSON)
EVENT_SET = load_json(cfg.JSON)
event = EVENT_SET['ak6569814836520190622']
# pprint(event)

queryEvent = edict(event.copy())
queryEvent['start_date'] = event['Ig_Date']
queryEvent['end_date'] = event['modisEndDate']
queryEvent['year'] = event['YEAR']

pprint(queryEvent)

queryEvent['roi'] = ee.Geometry.Polygon(event['roi']).bounds()

# Fire Period
period_start = ee.Date(queryEvent['start_date']).advance(-1, 'month')
period_end = ee.Date(queryEvent['start_date']).advance(2, 'month')
print(period_start.format().getInfo(), period_end.format().getInfo())


""" #################################################################
Query S2 MSI Data 
################################################################# """ 
S2_Dict = {
    'SR': "COPERNICUS/S2_SR",
    'TOA': "COPERNICUS/S2"
}

L8_Dict = {
    'SR': "LANDSAT/LC08/C01/T1_SR",
    'TOA': "LANDSAT/LC08/C01/T1_TOA"
}

MSI = ee.ImageCollection(S2_Dict['TOA']).filterBounds(queryEvent['roi'])
cloudFilter = ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 30)

MSI_pre = MSI.filterDate(period_start.advance(-1, 'year'), period_end.advance(-1, "year")).filter(cloudFilter).median()
MSI_post = MSI.filterDate(period_start.advance(1, 'year'), period_end.advance(1, "year")).filter(cloudFilter).median()


""" #################################################################
Query S1 SAR Data 
################################################################# """ 
def set_group_index_4_S1(img, groupLevel=13, labelShowLevel=13):
        orbitKey = (ee.String(img.get("orbitProperties_pass")).replace('DESCENDING', 'DSC').replace('ASCENDING', 'ASC')
                    .cat(ee.Number(img.get("relativeOrbitNumber_start")).int().format()))
        Date = (img.date().format().slice(0, labelShowLevel)
                    .replace('-', '').replace('-', '').replace(':', '').replace(':', ''))
        Name = (Date).cat('_').cat(orbitKey)

        groupIndex = img.date().format().slice(0, groupLevel)  # 2017 - 07 - 23T14:11:22(len: 19)
        return img.setMulti({
            'GROUP_INDEX': groupIndex,
            'IMG_LABEL': Name,
            'Orbit_Key': orbitKey
        })

def unionGeomFun(img, first):
    rightGeo = ee.Geometry(img.geometry())
    return ee.Geometry(first).union(rightGeo)

S1_flt = ee.ImageCollection(ee.ImageCollection("COPERNICUS/S1_GRD")
                        .filterBounds(queryEvent.roi)
                        .filterMetadata('instrumentMode', "equals", 'IW')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                    ).select(['VH', 'VV'])

S1_pre = S1_flt.filterDate(period_start.advance(-1, 'year'), period_end.advance(-1, "year")).map(set_group_index_4_S1)
S1_post = S1_flt.filterDate(period_start.advance(1, 'year'), period_end.advance(1, "year")).map(set_group_index_4_S1)

# SAR orbits
pre_orbits = S1_pre.aggregate_array("Orbit_Key").distinct().getInfo()
post_orbits = S1_post.aggregate_array("Orbit_Key").distinct().getInfo()
common_orbits = list(set(pre_orbits) & set(post_orbits))

# Compute average image for each orbit
S1 = {}
for orbit in common_orbits:
# for orbit in ['DSC160']:
    orbImgCol_pre = S1_pre.filter(ee.Filter.eq("Orbit_Key", orbit))#.sort("GROUP_INDEX", False)
    orbImgCol_post = S1_post.filter(ee.Filter.eq("Orbit_Key", orbit))#.sort("GROUP_INDEX", False)

    orb_images = orbImgCol_pre.filter(ee.Filter.eq("IMG_LABEL", orbImgCol_pre.first().get("IMG_LABEL")))
    firstImgGeom = orb_images.first().geometry()
    orb_geom = ee.Geometry(orb_images.iterate(unionGeomFun, firstImgGeom))

    if orb_geom.contains(queryEvent.roi, ee.ErrorMargin(1)).getInfo():
        S1[f"{orbit}_pre"] = orbImgCol_pre.mean()
        S1[f"{orbit}_post"] = orbImgCol_post.mean()

        # Map.addLayer(orb_geom, {}, f"{orbit}_geom")
        # Map.addLayer(S1[f"{orbit}_pre"], {"bands": ['VH'], "min":-20, "max": -10}, f"{orbit}_pre")
        # Map.addLayer(S1[f"{orbit}_post"], {"bands": ['VH'], "min":-20, "max": -10}, f"{orbit}_post")
        

""" #################################################################
Query ALOS SAR Data 
################################################################# """ 
# S1 = ee.ImageCollection()



""" #################################################################
Query Mask Data 
################################################################# """ 
# VIIRS Active Fire


# Fire Polygon


# MODIS Burned Area Map (500m) / FireCCI50 (250m)


# MTBS Burn Severity Mask




# WaterMask
""" =============== Froest Land Cover 2017 ================= """
landCover = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017")
landCover = ee.Image(landCover.select("discrete_classification").rename('CGLS').setMulti({'IMG_LABEL': 'CGLS'}))#.eq(mainLandCover)
waterMask0 = (landCover.neq(80).And(landCover.neq(200))).rename('water')



""" Export Both SAR and MSI to Cloud """