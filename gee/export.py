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


def update_query_event(cfg, event):
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

    return queryEvent


""" Query and Export """
def query_s1s2_and_export(queryEvent, scale=20, BUCKET="wildfire-dataset", dataset_folder='wildfire-s1s2-dataset-ca', export=['S1', 'S2', 'ALOS', 'mask', 'AUZ']):
    """
        queryEvent: the event info used to query data
        scale: the spatial resolution in meters, 20 as default
        BUCKET: Google Cloud Storage (GCS) Bucket, make sure it is available in your GCS
        dataset_folder: unique folder name for a specific task 
        export: a list including all data sources to export, S2, S1, and ALOS denote Sentinel-2, Sentinel-1, and ALOS PARSAR respectively. mask denotes the reference masks rasterized from official fire perimiters, or MODIS/VIIRS Montly Burned Area products, while AUZ denotes some auxiliary data, such as land cover, DEM/DSM or climate zone etc.
    """
        
        
    """ Event to Query """

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

    saveName = f"{queryEvent.name}"
    for sat in export_dict.keys():
        # for stage in export_dict[sat].keys():
        for stage in ['post']:
            dst_url = f"{dataset_folder}/{sat}/{stage}/{saveName}"

            if 'S1' == sat:
                for orbKey in export_dict[sat][stage]:
                    image = export_dict[sat][stage][orbKey]
                    print(f"{dst_url}_{orbKey}")
                    export_image_to_CloudStorage(image, queryEvent.roi, f"{dst_url}_{orbKey}", scale=scale, crs=queryEvent.crs, BUCKET=BUCKET)

            else:
                image = export_dict[sat][stage]
                print(dst_url)
                export_image_to_CloudStorage(image, queryEvent.roi, str(dst_url), scale=scale, crs=queryEvent.crs, BUCKET=BUCKET)
                

""" MODIS """
def query_modis_viirs_and_export(event, scale=500, BUCKET="wildfire-dataset", dataset_folder='wildfire-s1s2-dataset-ca', export_mask=True):
    # gee code: https:#code.earthengine.google.com/f7cd69c6b51d7b175a1550e2a06f296e

    event = edict(event)

    def add_ROI_Cloud_Rate(img):
        cloud = img.select('cloud')
        cloud_pixels = cloud.eq(0).reduceRegion(ee.Reducer.sum(), event.roi, 1000).get('cloud')
        all_pixels = cloud.gte(0).reduceRegion(ee.Reducer.sum(), event.roi, 1000).get('cloud')
        return img.set("ROI_CLOUD_RATE", ee.Number(cloud_pixels).divide(all_pixels).multiply(100))

    modis = ee.ImageCollection("MODIS/061/MOD09GA") # Terra (MOD) vs. Aqua (MYD)
    filtered_modis = (modis.filterDate(event.end_date, ee.Date(event.end_date).advance(30, 'day'))
                        .map(maskClouds)
                        .map(add_ROI_Cloud_Rate)
                        .filter(ee.Filter.lte("ROI_CLOUD_RATE", 10))
                        .map(maskEmptyPixels)
                )
    
    img_modis = filtered_modis.first()
    
    # modis mask (500m modis monthly vs. 250m modis daily)
    if 500 == scale:
        # MODIS
        mask_name = 'modis'
        mask = (ee.ImageCollection("MODIS/006/MCD64A1")
                    .filterDate(ee.Date(event.start_date).advance(-30, 'day'), ee.Date(event.end_date).advance(30, 'day'))
                    .mosaic()
                    .select('BurnDate').int16()
                    .unmask()
        )

    elif 250 == scale: 
        # Terra MODIS Data: merge Terra 250m and 500m            
        img_modis = filtered_modis.map(modis_terra_merger).first()

        # FireCCI51
        mask_name = 'firecci'
        mask = (ee.ImageCollection("ESA/CCI/FireCCI/5_1")
            .filterDate(ee.Date(event.start_date).advance(-30, 'day'), ee.Date(event.end_date).advance(30, 'day'))
            .mosaic()
            .select('BurnDate').int16()
            .unmask()
        )

    else:
        print("scale can only be 250m or 500m!")
        

    ''' Export '''
    saveName = f"{event.name}"
    export_image_to_CloudStorage(
        image=img_modis.select(['sur_refl_b01', 'sur_refl_b02', 'sur_refl_b07']).rename(['Red', 'NIR', 'SWIR']).int16(), 
        aoi=event.roi, 
        dst_url=f"{dataset_folder}/{'modis'}/{'post'}/{saveName}", 
        scale=scale, 
        crs=event.crs, 
        BUCKET=BUCKET
    )

    if export_mask:
        export_image_to_CloudStorage(
                image=mask.select(['BurnDate']).int16(), 
                aoi=event.roi, 
                dst_url=f"{dataset_folder}/{'mask'}/{mask_name}/{saveName}", 
                scale=scale, 
                crs=event.crs, 
                BUCKET=BUCKET
            )

    # VIIRS 500m Daily 
    # M11-SWIR (2.2), I3-SWIR1 (1.6), I2-NIR (0.865), I1-Red (0.640) 
    if False:
        # query viirs image based on modis image date                    
        image_date = img_modis.date()
        img_viirs = (ee.ImageCollection("NOAA/VIIRS/001/VNP09GA")
                            .filterDate(image_date, ee.Date(image_date).advance(1, 'day'))
                    ).first()

        export_image_to_CloudStorage(
            image=img_viirs.select(['I1', 'I2', 'M11']).rename(['Red', 'NIR', 'SWIR']).int16(), 
            aoi=event.roi, 
            dst_url=f"{dataset_folder}/{'viirs'}/{'post'}/{saveName}", 
            scale=scale, 
            crs=event.crs, 
            BUCKET=BUCKET
        )

    ##TODO: write codes for exporting modis progression / time series images
    if False:
        prgImgCol = (modis.filterDate(ee.Date(event.start_date).advance(-10, 'day'), ee.Date(event.end_date).advance(10, 'day'))
                        .map(maskClouds)
                        .map(add_ROI_Cloud_Rate)
                        .filter(ee.Filter.lte("ROI_CLOUD_RATE", 20))
                        .map(maskEmptyPixels)
                )
        img_num = prgImgCol.size().getInfo()
        print(f"\n--> MODIS Progression Images: {img_num} <--")
        imgList = prgImgCol.toList(img_num)

        for i in range(0, img_num):
            image = ee.Image(imgList.get(i))
            imgLabel = image.date().format().slice(0,10).replace("-",'_')

            export_image_to_CloudStorage(
                image=image.select(['sur_refl_b01', 'sur_refl_b02', 'sur_refl_b07']).rename(['Red', 'NIR', 'SWIR']).int16(), 
                aoi=event.roi, 
                dst_url=f"wildfire-modis-prg-dataset/{saveName}/{imgLabel}", 
                scale=scale, 
                crs=event.crs, 
                BUCKET=BUCKET
            )


# Modis Cloud Masking example.
# Calculate how frequently a location is labeled as clear (i.e. non-cloudy)
# according to the "internal cloud algorithm flag" of the MODIS "state 1km"
# QA band.

# A function to mask out pixels that did not have observations.
def maskEmptyPixels(image):
    # Find pixels that had observations.
    withObs = image.select('num_observations_1km').gt(0)
    return image.updateMask(withObs)

# A function to mask out cloudy pixels.
def maskClouds(image):
    # Select the QA band.
    QA = image.select('state_1km')
    # Make a mask to get bit 10, the internal_cloud_algorithm_flag bit.
    bitMask = 1 << 10
    # Return an image masking out cloudy areas.
    cloud_mask = QA.bitwiseAnd(bitMask).eq(0)
    # return image.updateMask(cloud_mask);
    return image.addBands(cloud_mask.rename('cloud'))

def modis_terra_merger(img):
    date = img.date()
    img_250m = ee.ImageCollection("MODIS/061/MOD09GQ").filterDate(date, ee.Date(date).advance(1, 'day')).first()
    return img.select('sur_refl_b07').addBands(img_250m.select(['sur_refl_b01', 'sur_refl_b02']))
