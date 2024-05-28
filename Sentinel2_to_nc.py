

#%%

# GEE: https://code.earthengine.google.com/3761eec6b55922cab60f26cb2eb4bf9b
import ee
from gee.group_data import group_MSI_ImgCol
from prettyprinter import pprint

ee.Initialize()

S2 = ee.ImageCollection("COPERNICUS/S2")  # This assumes Sentinel-2 Image Collection
roi = ee.Geometry.Polygon(
        [[[100.74280703529881, 30.341650698372668],
          [100.74280703529881, 29.850947604078836],
          [101.30997622475194, 29.850947604078836],
          [101.30997622475194, 30.341650698372668]]], None, False)

imgCol = (S2.filterBounds(roi)
          .filterDate('2024-03-22', '2024-03-23')
          .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 50))
        #   .map(add_SCL_mask)
          )

imgCol_grouped = group_MSI_ImgCol(imgCol, groupLevel='day')
pprint(imgCol_grouped.aggregate_array('IMG_LABEL').getInfo())

#%%
import xarray as xr
import numpy as np

crs = imgCol.first().select(0).projection().crs().getInfo()
ds = xr.open_dataset(
          imgCol_grouped, 
          engine='ee', 
          # projection=imgCol.first().select(0).projection(),
          crs=crs,
          geometry=roi,
          scale=10
      )

ds = ds.assign_coords(time=np.datetime_as_string(ds.coords['time'], unit='h'))
# ds.sel(time='2024-03-19T03').B12.T.plot.imshow()
ds.sel(time='2024-03-22T04').B12.T.plot.imshow()
ds

#%%
# https://code.earthengine.google.com/3761eec6b55922cab60f26cb2eb4bf9b
points = ee.FeatureCollection.randomPoints(roi, 10)
AOIs = points.map(lambda pnt: pnt.buffer(100).bounds())
patches = points.map(lambda pnt: imgCol_grouped.first().clip(ee.Geometry(pnt.buffer(128).bounds())))
patches = ee.ImageCollection(patches)

#%%
crs = imgCol.first().select(0).projection().crs().getInfo()
ds = xr.open_dataset(
          patches, 
          engine='ee', 
          # projection=imgCol.first().select(0).projection(),
          crs=crs,
          geometry=AOIs,
          scale=10
      )
ds
#%%

import geemap
Map = geemap.Map()

Map.addLayer(imgCol_grouped.first(), {'bands': ['B12','B8','B4'], 'min':0, 'max': 3000}, '03-22')
Map.addLayer(imgCol_grouped.first().geometry(), {}, 'geo')
Map.addLayer(roi, {}, 'roi')
Map.centerObject(roi, 8)
Map


#%%

imgList = imgCol_grouped.toList(imgCol_grouped.size())
image = imgCol_grouped.first()

def export_to_Drive(image):
  saveName = image.get('IMG_LABEL').getInfo()
  print(f"export {saveName}")

  task = ee.batch.Export.image.toDrive(
    image = image.toUint16(), 
    description = saveName, 
    folder='YaJiang', 
    fileNamePrefix=saveName, 
    region=roi, 
    scale=20, 
    crs='EPSG:32647', 
    # maxPixels=1e20
  )

  task.start()

for idx in range(0, imgCol_grouped.size().getInfo()):
  image = ee.Image(imgList.get(idx))
  export_to_Drive(image)