
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
    # BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'] # 6 bands
    BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12'] # 10 bands
    return (img.select(BANDS).toFloat()
                .divide(1e4).clamp(0,0.5).unitScale(0,0.5)
                .addBands(img.select('cloud'))
        ).copyProperties(img, img.propertyNames())

def get_s2_progression(queryEvent, cloud_level=10, filter_by_cloud=False):
    period_start = queryEvent.period_start
    period_end = queryEvent.period_end
    roi = queryEvent.roi

    def add_ROI_Cloud_Rate(img):
        cloud = img.select('cloud').updateMask(img.select(0).mask())
        cloud_pixels = cloud.eq(0).reduceRegion(ee.Reducer.sum(), roi, 60).get('cloud')
        all_pixels = cloud.gte(0).reduceRegion(ee.Reducer.sum(), roi, 60).get('cloud')
        return img.set("ROI_CLOUD_RATE", ee.Number(cloud_pixels).divide(all_pixels).multiply(100)).copyProperties(img, img.propertyNames())

    S2_Dict = {
        'SR': "COPERNICUS/S2_SR",
        'TOA': "COPERNICUS/S2"
    }

    L8_Dict = {
        'SR': "LANDSAT/LC08/C01/T1_SR",
        'TOA': "LANDSAT/LC08/C01/T1_TOA"
    }

    
    # cloudFilter = ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_level)
    cloudFilter = ee.Filter.lte("ROI_CLOUD_RATE", cloud_level)

    s2ImgCol = (ee.ImageCollection(S2_Dict['TOA'])
                    .filterBounds(queryEvent['roi'])
                    .filterDate(period_start, period_end)
                    .map(updateCloudMaskS2)
    )

    s2ImgCol_grouped = group_MSI_ImgCol(s2ImgCol)

    # mosaic s2 data acquired on the same day
    from gee.group_data import set_group_index_4_S2
    s2_prgImgCol = (s2ImgCol_grouped
                .map(set_group_index_4_S2)
                .map(add_ROI_Cloud_Rate)
                .map(rescale_s2)
            )
    
    if filter_by_cloud: s2_prgImgCol = s2_prgImgCol.filter(cloudFilter)
    return s2_prgImgCol

""" #################################################################
Query S1 SAR Data
################################################################# """ 

# Sentinel-1
from gee.group_data import group_MSI_ImgCol, group_S1_by_date_orbit, set_group_index_4_S1

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

def get_s1_progression(queryEvent):
    period_start = queryEvent.period_start
    period_end = queryEvent.period_end
    # start to query S1 data
    S1_flt = (ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(queryEvent.roi)
                .filterMetadata('instrumentMode', "equals", 'IW')
                .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                .filterDate(period_start, period_end)
                .select(['VH', 'VV'])
        )

    s1ImgCol_grouped = group_S1_by_date_orbit(S1_flt)
    s1ImgCol = (s1ImgCol_grouped
                    .map(add_RFDI)
                    .map(set_group_index_4_S1)
            )


    return s1ImgCol.select(['ND', 'VH', 'VV'])


""" #################################################################
Query ALOS L-Band SAR Data (No Data)
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
    modis = MODIS.filterDate(ee.Date(queryEvent.year), ee.Date(queryEvent.year).advance(1, 'year')).mosaic()
    # print("modis: ", modis.bandNames().getInfo())
    mask_dict['modis'] = modis.select('BurnDate').unmask()

    # FireCCI51
    FireCCI51 = ee.ImageCollection("ESA/CCI/FireCCI/5_1")
    firecci = FireCCI51.filterDate(ee.Date(queryEvent.year), ee.Date(queryEvent.year).advance(1, 'year')).mosaic()
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
        mtbs = ee.Image.loadGeoTIFF(f"gs://eo4wildfire/US_BurnSeverityRaster/mtbs_{WHERE}_{queryEvent.year}.tif")
        mask_dict['mtbs'] = mtbs.select('B0').rename('mtbs')

    if WHERE in ['CA']:
        pass

    if WHERE in ['EU']:
        pass

    return mask_dict


""" Export Progression """
from gee.aux_data import get_aux_dict
def query_progression_and_export(cfg, event, scale=20, BUCKET="wildfire-prg-dataset", export_sat=['S1', 'S2', 'mask', 'AUZ']):

    """ Event to Query """
    queryEvent = edict(event.copy())

    queryEvent['period_start'] = ee.Date(queryEvent['start_date']).advance(-1, 'month')
    queryEvent['period_end'] = ee.Date(queryEvent['end_date']).advance(1, 'month')
    queryEvent['roi'] = ee.Geometry.Polygon(event['roi']).bounds()

    # from gee.progression import get_s1_progression, get_s2_progression, get_mask_dict

    export_dict = edict({
            'S2': get_s2_progression(queryEvent, cloud_level=20, filter_by_cloud=False),
            'S1': get_s1_progression(queryEvent),
            # 'ALOS': get_alos_dict(queryEvent),
            'mask': get_mask_dict(queryEvent),
            'AUZ': get_aux_dict()
        })

    export_dict = {key: export_dict[key] for key in export_sat}
    pprint(export_dict)

    """ Export Both SAR and MSI to Cloud """
    from gee.export import export_image_to_CloudStorage

    event_folder = f"{event.name}"

    # Export Progression
    for sat in [sat_ for sat_ in ['S1', 'S2'] if sat_ in export_dict]:

        imgCol = export_dict[sat]

        img_num = imgCol.size().getInfo()
        print(f"\n--> {sat}: {img_num} <--")
        imgList = imgCol.toList(img_num)
        for i in range(0, img_num):
            image = ee.Image(imgList.get(i))
            imgLabel = image.get("IMG_LABEL").getInfo()
            dst_url = f"{event_folder}/{sat}/{imgLabel}"

            print(dst_url)
            export_image_to_CloudStorage(image, queryEvent.roi, str(dst_url), scale=scale, crs=queryEvent.crs, BUCKET=BUCKET)

    # Export Mask 
    for sat in [sat_ for sat_ in ["mask", "AUZ"] if sat_ in export_dict] :
        for stage in export_dict[sat].keys():
            mask = export_dict[sat][stage]
            dst_url = f"{event_folder}/{sat}/{stage}"

            print(dst_url, mask.bandNames().getInfo())
            export_image_to_CloudStorage(mask, queryEvent.roi, str(dst_url), scale=scale, crs=queryEvent.crs, BUCKET=BUCKET)
