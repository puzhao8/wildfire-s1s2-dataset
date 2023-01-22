
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


""" #################################################################
Query S2 MSI Data 
################################################################# """ 
def updateCloudMaskS2(img): 
    qa = img.select('QA60')  # 
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
        qa.bitwiseAnd(cirrusBitMask).eq(0)).rename('cloud')
    return img.addBands(mask, overwrite=True)


def rescale_s2(img): 
    BANDS = ['B4', 'B8', 'B12'] # 6 bands
    # BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'] # 6 bands
    # BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12'] # 10 bands
    return (img.select(BANDS)
                .toFloat()
                .divide(1e4).clamp(0,0.5).unitScale(0,0.5)
                # # .addBands(img.select('cloud'))
    )

def get_s2_dict(queryEvent, cloud_level=5):
    period_start = queryEvent.period_start
    period_end = queryEvent.period_end
    roi = queryEvent.roi

    def add_ROI_Cloud_Rate(img):
        cloud = img.select('cloud').updateMask(img.select(0).mask())
        cloud_pixels = cloud.eq(0).reduceRegion(ee.Reducer.sum(), roi, 60).get('cloud')
        all_pixels = cloud.gte(0).reduceRegion(ee.Reducer.sum(), roi, 60).get('cloud')
        return img.set("ROI_CLOUD_RATE", ee.Number(cloud_pixels).divide(all_pixels).multiply(100))

    S2_Dict = {
        'SR': "COPERNICUS/S2_SR",
        'TOA': "COPERNICUS/S2"
    }

    L8_Dict = {
        'SR': "LANDSAT/LC08/C01/T1_SR",
        'TOA': "LANDSAT/LC08/C01/T1_TOA"
    }

    MSI = ee.ImageCollection(S2_Dict['TOA']).filterBounds(queryEvent['roi'])
    # cloudFilter = ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_level)
    cloudFilter = ee.Filter.lte("ROI_CLOUD_RATE", cloud_level)

    print("post: ", period_start.advance(1, 'year').format().getInfo(), \
        period_end.advance(1, "year").format().getInfo())

    s2_dict = edict()
    # s2_dict['pre'] = (MSI.filterDate(period_start.advance(-1, 'year'), period_end.advance(-1, "year"))
    #                     .map(updateCloudMaskS2)
    #                     .map(add_ROI_Cloud_Rate)
    #                     .filter(cloudFilter)
    #                     .median()
    #                     # .sort("ROI_CLOUD_RATE", False).mosaic() # add on Oct. 10

    #                 )
    

    if queryEvent.end_date is not None:
        # post image in the same year
        s2_dict['post'] = (MSI.filterDate(queryEvent.end_date, ee.Date(queryEvent.end_date).advance(2,"month"))
                            .map(updateCloudMaskS2)
                            .map(add_ROI_Cloud_Rate)
                            .filter(cloudFilter)
                            .median()
                            # .sort("ROI_CLOUD_RATE", False).mosaic() # add on Oct. 10
                        )#.uint16()
    
    else: 
        # post image in next year
        s2_dict['post'] = (MSI.filterDate(period_start.advance(1, 'year'), period_end.advance(1, "year"))
                            .map(updateCloudMaskS2)
                            .map(add_ROI_Cloud_Rate)
                            .filter(cloudFilter)
                            .median()
                            # .sort("ROI_CLOUD_RATE", False).mosaic() # add on Oct. 10
                        )

    # s2_dict['cloud'] = None

    # rescale to [0, 1]
    # s2_dict['pre'] = rescale_s2(s2_dict['pre'])
    s2_dict['post'] = rescale_s2(s2_dict['post'])

    return s2_dict

""" #################################################################
Query S1 SAR Data
################################################################# """ 

# Sentinel-1
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

def toNatural(img):
    return ee.Image(10.0).pow(img.divide(10.0))

def toDB(img):
    return ee.Image(img).log10().multiply(10.0)

def add_RFDI(img):
    RFDI = toNatural(img.select(['VV','VH'])).normalizedDifference(['VV', 'VH']).select('nd').rename('ND')
    RFDI_dB = toDB(RFDI).multiply(10)

    return img.addBands(RFDI_dB).copyProperties(img, img.propertyNames())

def add_CR(img):
    return img.addBands(img.expression("b('VH')-b('VV')").rename('CR'))

def get_s1_dict(queryEvent):
    period_start = queryEvent.period_start
    period_end = queryEvent.period_end
    # start to query S1 data
    S1_flt = ee.ImageCollection(ee.ImageCollection("COPERNICUS/S1_GRD")
                            .filterBounds(queryEvent.roi)
                            .filterMetadata('instrumentMode', "equals", 'IW')
                            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                        ).select(['VH', 'VV'])


    S1_pre = (S1_flt.filterDate(period_start.advance(-1, 'year'), period_end.advance(-1, "year"))
                    .map(add_RFDI)
                    .map(set_group_index_4_S1)
            )

    if queryEvent.end_date is not None:
        # post s1 image in the same year
        S1_post = (S1_flt.filterDate(queryEvent.end_date, ee.Date(queryEvent.end_date).advance(2,"month"))
                        .map(add_RFDI)
                        .map(set_group_index_4_S1)
                )

    else:
        # post s1 image in the next year
        S1_post = (S1_flt.filterDate(period_start.advance(1, 'year'), period_end.advance(1, "year"))
                        .map(add_RFDI)
                        .map(set_group_index_4_S1)
                )

    # if S1_pre.size().getInfo() == 0: #if there is no images in the before-year
    #      S1_pre = (S1_flt.filterDate(period_start.advance(-2, 'month'), period_start)
    #                 .map(add_RFDI)
    #                 .map(set_group_index_4_S1)
    #         )

    if S1_post.size().getInfo() == 0: #if there is no images in the after-year
         S1_post = (S1_flt.filterDate(queryEvent['end_date'], ee.Date(queryEvent['end_date']).advance(2, 'month'))
                    .map(add_RFDI)
                    .map(set_group_index_4_S1)
            )

    # SAR orbits
    pre_orbits = S1_pre.aggregate_array("Orbit_Key").distinct().getInfo()
    post_orbits = S1_post.aggregate_array("Orbit_Key").distinct().getInfo()
    common_orbits = list(set(pre_orbits) & set(post_orbits))

    # Compute average image for each orbit
    S1_dict = edict({'pre':{}, 'post': {}})
    for orbit in common_orbits:
    # for orbit in ['DSC160']:
        orbImgCol_pre = S1_pre.filter(ee.Filter.eq("Orbit_Key", orbit))#.sort("GROUP_INDEX", False)
        orbImgCol_post = S1_post.filter(ee.Filter.eq("Orbit_Key", orbit))#.sort("GROUP_INDEX", False)

        orb_images = orbImgCol_pre.filter(ee.Filter.eq("IMG_LABEL", orbImgCol_pre.first().get("IMG_LABEL")))
        firstImgGeom = orb_images.first().geometry()
        orb_geom = ee.Geometry(orb_images.iterate(unionGeomFun, firstImgGeom))

        if orb_geom.contains(queryEvent.roi.buffer(-1e3), ee.ErrorMargin(1)).getInfo():
            S1_dict['pre'][f"{orbit}"] = orbImgCol_pre.mean().select(['ND', 'VH', 'VV'])
            S1_dict['post'][f"{orbit}"] = orbImgCol_post.mean().select(['ND', 'VH', 'VV'])

    return S1_dict


""" #################################################################
Query ALOS L-Band SAR Data
################################################################# """ 

# def toDB(img):
#     return ee.Image(img).log10().multiply(10.0)
    
def add_ALOS_RFDI(img):
    RFDI = img.select(['HH','HV']).normalizedDifference(['HH','HV']).select('nd').rename('ND')
    RFDI_dB = toDB(RFDI).multiply(3)
    return img.addBands(RFDI_dB)

def to_ALOS_dB(img):
    return img.addBands(img.select(['HH', 'HV']).pow(ee.Image(2)).log10().multiply(10).subtract(83), ['HH', 'HV'], True)

def add_ALOS_CR(img):
    return img.addBands(img.expression("b('HV')-b('HH')").rename('CR'))


# ALOS
def get_alos_dict(queryEvent):
    PALSAR = ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR")
    PALSAR_dB = PALSAR.map(add_ALOS_RFDI).map(to_ALOS_dB)#.map(add_ALOS_CR)

    before_year = ee.Number.parse(queryEvent.year).subtract(1).format().getInfo()
    after_year = ee.Number.parse(queryEvent.year).add(1).format().getInfo()

    ALOS_pre = PALSAR_dB.filter(ee.Filter.eq("system:index", before_year)).first()
    ALOS_post = PALSAR_dB.filter(ee.Filter.eq("system:index", after_year)).first()

    ALOS = edict()
    ALOS['pre'] = ALOS_pre.select(["ND", "HV", "HH"])
    ALOS['post'] = ALOS_post.select(["ND", "HV", "HH"])

    return ALOS

""" #################################################################
Query Mask Data 
################################################################# """ 
def get_mask_dict(queryEvent):
    mask_dict = edict()
    WHERE = queryEvent['where']

    # MODIS
    MODIS = ee.ImageCollection("MODIS/006/MCD64A1")
    modis = MODIS.filterDate(ee.Date(queryEvent.start_date).advance(-10, 'day'), ee.Date(queryEvent.end_date).advance(10, 'day')).mosaic()
    # print("modis: ", modis.bandNames().getInfo())
    mask_dict['modis'] = modis.select('BurnDate').unmask()

    # FireCCI51
    FireCCI51 = ee.ImageCollection("ESA/CCI/FireCCI/5_1")
    firecci = FireCCI51.filterDate(ee.Date(queryEvent.start_date).advance(-10, 'day'), ee.Date(queryEvent.end_date).advance(10, 'day')).mosaic()

    # print("firecci: ", firecci.bandNames().getInfo())
    mask_dict['firecci'] = firecci.select('BurnDate').unmask()

    # # Water (see aux_data.py)
    # landCover = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017")
    # landCover = ee.Image(landCover.select("discrete_classification").rename('CGLS').setMulti({'IMG_LABEL': 'CGLS'}))
    # water = (landCover.neq(80).And(landCover.neq(200))).rename('water')
    # mask_dict['water'] = water

    # Polygon
    if WHERE in ['AK', 'US']:
        print(WHERE)

        # USA
        US_bef_2018 = ee.FeatureCollection("users/omegazhangpzh/C_US_Fire_Perimeters/US_HIST_FIRE_PERIMTRS_2000_2018_DD83")
        US_2019 = ee.FeatureCollection("users/omegazhangpzh/C_US_Fire_Perimeters/US_HIST_FIRE_PERIM_2019_dd83")
        poly = (US_bef_2018.filterBounds(queryEvent.roi).filter(ee.Filter.gte("fireyear", 2017))
                    .merge(US_2019.filterBounds(queryEvent.roi))
                    # .filter(ee.Filter.gte("gisacres", 5000)) # burned area
                ).union(ee.ErrorMargin(30))
        polyImg = poly.style(color='white', fillColor='white', width=0).select('vis-red').gt(0).rename('poly')
        mask_dict['poly'] = polyImg.unmask()
                    
        # USA MTBS
        WHERE = "CONUS" if WHERE == "US" else "AK"
        mtbs = ee.Image.loadGeoTIFF(f"gs://sar4wildfire/US_BurnSeverityRaster/mtbs_{WHERE}_{queryEvent.year}.tif")
        mask_dict['mtbs'] = mtbs.select('B0').rename('mtbs')
    

    if 'CA' in WHERE:
        # CA
        CA_2017 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2017_r9_20190919")
        CA_2018 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2018_r9_20200703")
        CA_2019 = ee.FeatureCollection("users/omegazhangpzh/Canada_Fire_Perimeters/nbac_2019_r9_20200703")  
        CA_BurnAreaPolys = CA_2017.merge(CA_2018).merge(CA_2019)

        poly = (CA_BurnAreaPolys.filterBounds(queryEvent.roi)
                        .filter(ee.Filter.gte("year", queryEvent.year))
                ).union(ee.ErrorMargin(30))
        polyImg = poly.style(color='white', fillColor='white', width=0).select('vis-red').gt(0).rename('poly')
        mask_dict['poly'] = polyImg.unmask()


    if WHERE in ['EU']:
        pass

    return mask_dict