
#%%

import ee
import xarray as xr
from easydict import EasyDict as edict

ee.Initialize()

event_dict = edict({
    'US_2021_Dixie': {
        "name": "US_2021_Dixie_V3",
        "roi": [-121.75405666134564,39.5671341526342,
                -119.88638088009564,40.92552027566895],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-06-16",
        "modisEndDate": "2021-09-17",

        "where": 'US'}
    })


event = event_dict['US_2021_Dixie']
event['roi'] = ee.Geometry.Rectangle(event.roi)


modisImgCol = (ee.ImageCollection("MODIS/061/MOD09GA")
            .filterBounds(ee.Geometry.Rectangle(event.roi))
            .filterDate(event.modisStartDate, ee.Date(event.modisEndDate).advance(30, 'day'))
          )
                         


#%%
# ds = xr.open_dataset(modisImgCol, 
#                          engine='ee', 
#                         #  projection=i.first().select(0).projection(),
#                          crs='EPSG:32610',
#                         #  geometry= i.first().geometry(),
#                          geometry=event.roi,
#                          scale=500
#                     )

# ds

#%%

from gee.group_data import group_MSI_ImgCol

def get_pntsFilter(roi, buffer_size=0):
    ## ==> Point Filters <==
    pnt_roi = roi.buffer(buffer_size, ee.ErrorMargin(1)).bounds()
    coordList = ee.List(pnt_roi.coordinates().get(0))
    btmLeft = ee.Geometry.Point(coordList.get(0))
    btmRight = ee.Geometry.Point(coordList.get(1))
    topRight = ee.Geometry.Point(coordList.get(2))
    topLeft = ee.Geometry.Point(coordList.get(3))

    # if len(pntsList) > 0:
    pntsFilter = ee.Filter.And(
        # ee.Filter.geometry(btmLeft),
        ee.Filter.geometry(btmRight),
        # ee.Filter.geometry(topRight),
        ee.Filter.geometry(topLeft)
    )

    return pntsFilter


cloudFilter = ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 20)
# cloudFilter = ee.Filter.lte("ROI_CLOUD_RATE", 20)

s2ImgCol = (ee.ImageCollection("COPERNICUS/S2_SR")
                .filterBounds(event.roi)
                .filterDate(event.modisStartDate, ee.Date(event.modisEndDate).advance(1, 'day'))
                .filter(cloudFilter)
                # .map(updateCloudMaskS2)
)


s2ImgCol_grouped = group_MSI_ImgCol(s2ImgCol)
check_img = s2ImgCol_grouped.filterDate("2021-09-16", "2021-09-17").first()

#%%
import geemap

Map = geemap.Map()

Map.addLayer(check_img, {'bands': ['B12', 'B8', 'B4'], 'min': 0, 'max':2000}, 'check_img')
Map.addLayer(check_img.geometry(), {}, 'geom')
Map.addLayer(event.roi, {}, 'roi')
Map

#%%
import numpy as np

ds = xr.open_dataset(
    # s2ImgCol_grouped,
    ee.ImageCollection([check_img]), 
                         engine='ee', 
                        #  projection=check_img.select(0).projection(),
                         crs='EPSG:32610',
                        #  geometry= i.first().geometry(),
                         geometry=event.roi,
                         scale=100
                    )
ds = ds.assign_coords(time=np.datetime_as_string(ds.coords['time'], unit='h'))
ds.sel(time='2021-09-16T19').B12.T.plot.imshow()
ds
