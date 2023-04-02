# from ee_preprocessing_funs import *
import ee
from easydict import EasyDict as edict


class MODIS_POLY:
  def __init__(self, cfg):
    self.cfg = cfg

    if len(self.cfg.roi) == 2:
      self.cfg.roi = ee.Geometry.Rectangle(self.cfg.roi)
    else:
      self.cfg.roi = ee.Geometry.Polygon(self.cfg.roi)

    self.modis = ee.ImageCollection("MODIS/006/MCD64A1")
    self.FireCCI51 = ee.ImageCollection("ESA/CCI/FireCCI/5_1")

    self.roiPoly = ee.FeatureCollection(self.cfg.roi).style(color='red', fillColor='#ff000000')
  
  def set_pntsFilter(self, polyBox):
    ## ==> Point Filters <==
    coordList = ee.List(polyBox.coordinates().get(0))
    # print(coordList)
    p1 = ee.Geometry.Point(coordList.get(0))
    p2 = ee.Geometry.Point(coordList.get(1))
    p3 = ee.Geometry.Point(coordList.get(2))
    p4 = ee.Geometry.Point(coordList.get(3))
    self.pntsFC = ee.FeatureCollection([p1, p2, p3, p4]).style(color="red")

    self.pntsFilter = ee.Filter.And(
          ee.Filter.geometry(p1),
          ee.Filter.geometry(p2),
          ee.Filter.geometry(p3),
          ee.Filter.geometry(p4))

  def gen_polyCol_from_modis(self):
    self.yearFirstDay = ee.Date(ee.Number(self.cfg.year).format().cat("-01-01"))
    self.yearEndDay = ee.Date(ee.Number(self.cfg.year).add(1).format().cat("-01-01"))

    modis_imgCol = self.modis.filterDate(self.yearFirstDay, self.yearEndDay)
    self.modisYearlyMosaic = modis_imgCol.mosaic().select('BurnDate')

    # Burn Map estimated by fusing modis and fireCCI 
    fireCCI_imgCol = self.FireCCI51.filterDate(self.yearFirstDay, self.yearEndDay)
    self.firecciYearlyMosaic = fireCCI_imgCol.mosaic().select('BurnDate')
  
    fusedYearlyMosaic = self.firecciYearlyMosaic.gt(0).unmask().Or(self.modisYearlyMosaic.gt(0).unmask())
    self.firecci_modis_fusedMask = fusedYearlyMosaic.mask(fusedYearlyMosaic.eq(1))

  def convert_burnDateImg_toPolyCol(self, burnDateImg):
      # # Convert burn areas into Polygons
      # self.burnDateImg = ee.Image(self.modisYearlyMosaic)
      # self.burnDateImg.mode = 'modisYearlyMosaic'

      # self.burnDateImg = ee.Image(self.firecciYearlyMosaic)
      # self.burnDateImg.mode = 'firecciYearlyMosaic'
      self.burnDateImg = burnDateImg
      polyFeatCol = (ee.Image(self.burnDateImg.gte(0)) 
                .reduceToVectors(geometry=self.cfg.roi, maxPixels=5094397829, scale=200) 
                .map(self.func_dissolve))

      # Compute inPoly area and set BurnDate
      self.polyCol = (polyFeatCol.map(self.compute_polyArea) 
                            .filter(ee.Filter.gte('area', self.cfg.modis_min_area)) 
                            .map(self.setBurnDate) 
                            .sort('area', False))

      self.polyNum = self.polyCol.size()
    

  def __call__(self):
      self.gen_polyCol_from_modis()
      self.union_polyCol_inside_roi()


  def union_polyCol_inside_roi(self):
      """ Union PolyCol """
      self.convert_burnDateImg_toPolyCol(self.modisYearlyMosaic)
      self.unionPoly = self.polyCol.union()

      self.unionPoly.startDate = (self.polyCol.reduceColumns(ee.Reducer.min(), ['startDate']).get('min')                                      .getInfo())
      self.unionPoly.endDate = self.polyCol.reduceColumns(ee.Reducer.max(), ['endDate']).get('max').getInfo()
      
      print("--------------- modis ---------------")
      # print(f"unionPoly.startDate: {self.unionPoly.startDate}, \nunionPoly.endDate: {self.unionPoly.endDate}")
      print(f"modis.startDate: {self.unionPoly.startDate}, \nmodis.endDate: {self.unionPoly.endDate}")
      print("-------------------------------------")


  def get_single_fireEvent(self, idxPoly):
      # Quary images according to derived polyBox from polyCol.
      polyList = self.polyCol.toList(self.polyCol.size())

      # idxPoly = 0     # idx-th largest wildfire in the specified ROI
      polyFeat = ee.Feature(polyList.get(idxPoly))
      self.single_fire = edict()
      self.single_fire.polyBox = polyFeat.bounds().geometry()
      self.single_fire.poly = ee.FeatureCollection([polyFeat])
      self.single_fire.startDate = ee.Date(polyFeat.get('startDate'))
      self.single_fire.endDate = ee.Date(polyFeat.get('endDate'))

      return self.single_fire


  def func_dissolve(self, feat):
      return feat.dissolve(maxError=200, proj=self.cfg.crs)

  # compute the cloud-coverage in polygon
  def computeCloudCoverInPoly(self, img, poly):
      cloudImg = ee.Image(img.select("QA60")).gte(1024)
      cloudAreaInPoly = self.compute_imgArea(cloudImg, poly)
      cloudCoverInPoly = cloudAreaInPoly.divide(ee.Number(polyFeat.get("area"))).multiply(100).round()
      return img.setMulti({'CLOUD_COVERAGE_INPOLY': self.cfg.cloudCoverageInPolyLevel})

  ###############################################/
  def compute_imgArea(self, img):
      areaHa = img.multiply(ee.Image.pixelArea()).divide(10000);#convert to "ha"
      stats = areaHa.reduceRegion(
            reducer = ee.Reducer.sum(),
            geometry = self.cfg.roi,
            scale = 100,
            maxPixels = 86062013
          )
      return ee.Number(stats.values().get(0)).round()

  def compute_polyArea(self, poly):
      polyFeatCol = ee.FeatureCollection([poly])
      img = polyFeatCol.style(color='white', fillColor='white', width=0) \
              .select('vis-red').gt(0).rename('poly')
      areaHa = img.multiply(ee.Image.pixelArea()).divide(10000) #convert to "ha"
      stats = areaHa.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=polyFeatCol.geometry(),
            scale=100,
            maxPixels=86062013
          )
      return ee.Feature(poly).setMulti({'area': ee.Number(stats.values().get(0)).round()})


  def setBurnDate(self, feat):
      burnDate = self.burnDateImg.reduceRegion(
        # reducer = ee.Reducer.minMax(),
        reducer = ee.Reducer.percentile([0.1, 99.9], ["min", "max"]), # BurnDate is more accurate using percentile
        scale = 100,
        geometry = ee.FeatureCollection([feat]).geometry()
      )
      BurnDate_min = burnDate.get("BurnDate_min")
      BurnDate_max = burnDate.get("BurnDate_max")

      startDate = self.yearFirstDay \
                .advance(ee.Number(BurnDate_min).subtract(1), 'day').format().slice(0,10)
      endDate = self.yearFirstDay \
                .advance(ee.Number(BurnDate_max).subtract(1), 'day').format().slice(0,10)

      return feat.setMulti({
                      'BurnDate_min': BurnDate_min,
                      'BurnDate_max': BurnDate_max,
                      'startDate': startDate,
                      'endDate': endDate
                  })

  
  def img2poly(self, img):
      # transform image into polygon
      img = img.reduce(ee.Reducer.anyNonZero())
      poly = img.reduceToVectors({
        'geometry': self.cfg.roi,
        'scale': 100,
        'crs': self.cfg.crs,
        'geometryType': 'polygon',
        'maxPixels': 20000000,
        'geometryInNativeProjection':True
      })
      poly = ee.FeatureCollection(poly)

      return poly

  def compute_area(self, img):
      areaHa = img.gt(0).multiply(ee.Image.pixelArea()).divide(10000) #convert to "ha"
      stats = areaHa.reduceRegion({
        'reducer': ee.Reducer.sum(),
        'geometry': self.cfg.roi,
        'scale': 50,
        'maxPixels': 86062013
      })
      return stats




