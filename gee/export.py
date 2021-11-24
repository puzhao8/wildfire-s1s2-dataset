from gee.aux_data import get_aux_dict
from gee.s1s2 import get_alos_dict
import os
import ee

import logging
logger = logging.getLogger(__name__)


def check_export_task(task, imgName):
        import time
        # Block until the task completes.
        logger.info('Running export from GEE to drive or cloudStorage...')
        while task.active():
            time.sleep(30)

        # Error condition
        if task.status()['state'] != 'COMPLETED':
            logger.info("Error with export: {}".format(imgName))
        else:
            logger.info("Export completed: {}".format(imgName))
        logger.info("---------------------------------------------------")


def export_image_to_CloudStorage(image, aoi, dst_url, scale=20, crs="EPSG:4326", BUCKET="wildfire-s1s2-dataset"):
        
    """ Run the image export task.  Block until complete """
    task = ee.batch.Export.image.toCloudStorage(
        image = image.toFloat(), 
        description = os.path.split(dst_url)[-1], 
        bucket = BUCKET, 
        # folder = f"{self.driveFolder}",
        fileNamePrefix = str(dst_url), 
        region = aoi, #.getInfo()['coordinates'], 
        scale = scale, 
        crs = crs,
        fileFormat = 'GeoTIFF', 
        maxPixels = 1e10,
        formatOptions = { # Cloud-Optimized TIF
            "cloudOptimized": True
        }
    )
    task.start()
    check_export_task(task, dst_url)


from prettyprinter import pprint
from easydict import EasyDict as edict


""" Query and Export """
def query_s1s2_and_export(cfg, event, scale=20, BUCKET="wildfire-s1s2-dataset", export=['S1', 'S2', 'ALOS', 'mask', 'AUZ']):
    """ Event to Query """
    queryEvent = edict(event.copy())
    # pprint(queryEvent)

    # pprint(queryEvent.roi)
    if event['where'] in ['AK', 'US']:
        burned_area = queryEvent['BurnBndAc'] * 0.4047 # to ha
    
    if 'CA' in event['where']:
        burned_area = queryEvent['ADJ_HA']

    if len(event['roi']) == 2: # if two points provided .. 
        queryEvent['roi'] = ee.Geometry.Rectangle(event['roi']).bounds()
    else: # if five points provided ...
        queryEvent['roi'] = ee.Geometry.Polygon(event['roi']).bounds()
    
    if burned_area <= 5000: # minimum roi 
        print("==> queryEvent['BurnBndAc'] < 2000ha")
        queryEvent['roi'] = queryEvent['roi'].centroid(ee.ErrorMargin(30)).buffer(10240).bounds()
    
    queryEvent.roi = queryEvent.roi.buffer(2e3).bounds() # added on July-03-2021
    pprint(queryEvent.roi.getInfo()['coordinates'])

    # fire period
    if 'fire_period' in cfg.period:
        queryEvent['period_start'] = ee.Date(queryEvent['start_date']).advance(-1, 'month')
        queryEvent['period_end'] = ee.Date(queryEvent['start_date']).advance(2, 'month')

    # season period
    if 'season' in cfg.period:
        queryEvent['period_start'] = ee.Date(queryEvent['year']).advance(cfg.season[0], 'month')
        queryEvent['period_end'] = ee.Date(queryEvent['year']).advance(cfg.season[-1], 'month')

    print("---> Fire Period <---")
    print(queryEvent['start_date'], queryEvent['end_date'])

    """ Query Data: S1, S2, & ALOS """
    from gee.s1s2 import get_s2_dict, get_s1_dict, get_mask_dict
    from gee.aux_data import get_aux_dict

    # pprint(queryEvent.roi.getInfo()['coordinates'])
    export_dict = edict({
        'S2': get_s2_dict(queryEvent, cloud_level=10),
        'S1': get_s1_dict(queryEvent),
        # 'ALOS': get_alos_dict(queryEvent),
        # 'mask': get_mask_dict(queryEvent),
        # 'AUZ': get_aux_dict()
    })
    
    export_dict = {key: export_dict[key] for key in export}
    pprint(export_dict)

    """ Export Both SAR and MSI to Cloud """
    from gee.export import export_image_to_CloudStorage

    saveName = f"{event.name}"
    for sat in export_dict.keys():
        # for stage in export_dict[sat].keys():
        for stage in ['post']:
            dst_url = f"{sat}/{stage}/{saveName}"

            if 'S1' == sat:
                for orbKey in export_dict[sat][stage]:
                    image = export_dict[sat][stage][orbKey]
                    print(f"{dst_url}_{orbKey}")
                    export_image_to_CloudStorage(image, queryEvent.roi, f"{dst_url}_{orbKey}", scale=scale, crs=queryEvent.crs, BUCKET=BUCKET)

            else:
                image = export_dict[sat][stage]
                print(dst_url)
                export_image_to_CloudStorage(image, queryEvent.roi, str(dst_url), scale=scale, crs=queryEvent.crs, BUCKET=BUCKET)
                


    
