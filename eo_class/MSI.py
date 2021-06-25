import ee
from eo_class.eo_dataset import EO_DATASET
# from Landsat8 import LANDSAT8
# from Sentinel2 import SENTINEL2

import logging
logger = logging.getLogger(__name__)

def compuate_area_from_image(img, roi):
    areaHa = img.multiply(ee.Image.pixelArea()).divide(10000)
    stats = areaHa.reduceRegion(
            reducer = ee.Reducer.sum(),
            geometry = roi,
            scale = 100,
            maxPixels = 86062013
        )
    area = ee.Number(stats.values().get(0)).round()
    return area

class MSI(EO_DATASET):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.cfg = cfg
        self.driveFolder = f"{self.driveFolder}/MSI"
        
        self.use_L8_Flag = cfg.use_L8_Flag
        self.dNBR_Flag = cfg.msi_dNBR_Flag

        self.msiMasterMode = cfg.msiMasterMode
        self.waterMaskFlag = cfg.waterMaskFlag

        self.roi_img = ee.Image(ee.FeatureCollection(self.roi)
                .style(color='white', fillColor='white')
                .select('vis-red').gt(0).rename('roi')
                .setMulti({'system:footprint': self.roi}))
        # self.roi_area = compuate_area_from_image(roi_img, self.roi)

    def query_wo_processing(self):
        logger.info("\n---------------- Sentinel-2/Landsat-8 ------------------------")
        logger.info(f"Check DateRange: [{self.checkStartDate.format().slice(0,10).getInfo()}, {self.checkEndDate.format().slice(0,10).getInfo()}]")

        S2 = SENTINEL2(self.cfg)
        S2.query_s2_wo_processing()
        self.msiImgCol = S2.S2_grouped.sort('IMG_LABEL', True)
        
        if self.use_L8_Flag: 
            L8 = LANDSAT8(self.cfg)
            L8.query_l8_wo_processing()
            self.msiImgCol = self.msiImgCol.merge(L8.L8_grouped).sort('IMG_LABEL', True)

        self.msiImgCol = (self.msiImgCol
                            .map(self.msiRescaleToOne)
                            .map(self.add_NBR)
                            .sort('IMG_LABEL', True)
                            .map(self.add_roi_cloud_rate)
                            # .map(lambda img: img.set("IMG_LABEL", \
                            #     ee.String(ee.String(img.get("IMG_LABEL")).cat("_"))\
                            #         .cat(ee.Number(img.get("ROI_CLOUD_RATE")).round()\
                            #         .format().split(".")[0])))
                        )

        
    def query_and_processing(self):
        logger.info("\n---------------- Sentinel-2/Landsat-8 ------------------------")
        
        Sentinel2 = SENTINEL2(self.cfg)
        Sentinel2()

        self.S2_grouped = Sentinel2.S2_grouped
        msiImgCol = (self.S2_grouped
                        # .merge(self.L8_grouped)
                        # .map(maskClouds)
                        ).sort('IMG_LABEL', True)

        self.S2_SCL = Sentinel2.S2_SCL

        if self.use_L8_Flag: 
            Landsat8 = LANDSAT8(self.cfg)
            Landsat8()
            self.L8_grouped = Landsat8.L8_grouped
            msiImgCol = msiImgCol.merge(self.L8_grouped).sort('IMG_LABEL', True)

        # self.printList(msiImgCol.aggregate_array('IMG_LABEL').getInfo(), "msiImgCol before pntsFilter")
        self.msiImgCol = (msiImgCol
                            .map(self.msiRescaleToOne)
                            .map(self.add_NBR)
                            .sort('IMG_LABEL', True)
                            .map(self.add_roi_cloud_rate)
                        )
    
        print("----------------------------------------------------------------------")
        """ if there is no need to do dNBR, stop here """
        if not self.dNBR_Flag: 
            print("===> MS BANDS: {}".format(self.msiImgCol.first().bandNames().getInfo()))
            return 

        """----------> select specified image as msiMasterImg: <------------"""
        if self.msiMasterMode == 'master':
            ### MS Master Image
            msiMasterDate = self.cfg.fireEvent['S2_Master']
            if 'elephant' in self.cfg.fireEvent['name']:
                msiMasterDate = self.cfg.fireEvent['L8_Master']

            print(f"msiMasterMode is: {self.msiMasterMode}")
            self.msiMasterImg = ee.Image(self.msiImgCol.filterDate(ee.Date(msiMasterDate), ee.Date(msiMasterDate).advance(1, 'day')).first())
        
        """----------> median of images within a given period as msiMasterImg: <------------"""
        logger.info(f"msiMasterMode is: {self.msiMasterMode}")
        if self.msiMasterMode == 'median':
            print(f"msiMasterMode is: {self.msiMasterMode}")
            msiPrefireTimeSeries = (self.msiImgCol
                        .filterDate(ee.Date(self.fireStartDate).advance(-1, 'month'), ee.Date(self.fireStartDate).advance(1, 'day'))
                        # .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 20))
                    )
                            
            for roi_cloud_rate in [1, 2, 5, 10, 20, 30, 50]:
                msiPrefireTimeSeries_flt = msiPrefireTimeSeries.filter(ee.Filter.lte("ROI_CLOUD_RATE", roi_cloud_rate))
                if msiPrefireTimeSeries_flt.size().getInfo() > 1: 
                    print(f"msiPrefireTimeSeries -> roi_cloud_ratio {roi_cloud_rate}: {msiPrefireTimeSeries_flt.size().getInfo()}")
                    logger.info(f"msiPrefireTimeSeries -> roi_cloud_ratio {roi_cloud_rate}: {msiPrefireTimeSeries_flt.size().getInfo()}")
                    break

            if msiPrefireTimeSeries_flt.size().getInfo() < 3:
                msiMasterImg = msiPrefireTimeSeries_flt.sort("ROI_CLOUD_RATE", True).first()
            else:
                try:
                    msiMasterImg = msiPrefireTimeSeries_flt.reduce(ee.Reducer.median())
                except:
                    print(f"length of msiPrefireTimeSeries: {msiPrefireTimeSeries_flt.size().getInfo()}")

            medianBandNameList = msiMasterImg.bandNames().getInfo()
            newBandNameList = [ele.split("_")[0] for ele in medianBandNameList]
            self.msiMasterImg = msiMasterImg.select(medianBandNameList).rename(newBandNameList)

        self.msiImgCol = self.msiImgCol.map(self.add_dNBR)

        # self.msiImgLabelList = self.msiImgCol.aggregate_array('IMG_LABEL').getInfo()
        print("===> MS BANDS: {}".format(self.msiImgCol.first().bandNames().getInfo()))
    
    def add_dNBR(self, slaveImg):
        dNBR = ee.Image(self.msiMasterImg.subtract(slaveImg)
                    .select(['NBR', 'NBR1']).rename(['dNBR', 'dNBR1']))
        
        if self.waterMaskFlag: # mask water
            dNBR = self.mask_water(dNBR)

        RdNBR = (dNBR.select(['dNBR', 'dNBR1']).rename(['NBR', 'NBR1']).multiply(1000)
                    .divide(self.msiMasterImg.select(['NBR', 'NBR1']).abs().sqrt())
                    .select(['NBR', 'NBR1']).rename(['RdNBR', 'RdNBR1'])
                )

        return (slaveImg.addBands(dNBR).addBands(RdNBR)
                        .copyProperties(slaveImg, slaveImg.propertyNames())
                )

    """ Preprocessing Funs for MS Images """
    def add_NDVI(self, img):
        NDVI = img.normalizedDifference(['NIR', 'R']).select('nd').rename('NDVI')
        return img.addBands(NDVI).copyProperties(img, img.propertyNames())

    """ To 8-bit """
    def to8bit(self, img): 
        mmax = 1
        return (img.clamp((-1)*mmax, mmax)
                    .add(mmax).divide(2*mmax).multiply(255).toUint8()
                    .toFloat().divide(255).multiply(2*mmax).subtract(mmax)
                    .setMulti({"IMG_LABEL": img.get("IMG_LABEL")})
                )

    def add_NBR(self, img):
        NBR = img.normalizedDifference(['NIR', 'SWIR2']).select('nd').rename('NBR')
        NBR1 = img.normalizedDifference(['SWIR1', 'SWIR2']).select('nd').rename('NBR1')
        # return img.addBands(NBR).addBands(NBR1).copyProperties(img, img.propertyNames())
        return img.addBands(self.to8bit(NBR)).addBands(self.to8bit(NBR1)).copyProperties(img, img.propertyNames())


    def msiRescaleToOne(self, img):
        return (img.select('cloud').addBands(
                        img.select(['R', 'G', 'B', 'NIR', 'SWIR1', 'PAN', 'SWIR2'])
                            .clamp(0, 0.5).unitScale(0, 0.5).float()
                        )    #.toUint8()
                                # .copyProperties(img, img.propertyNames())
                )

    def set_group_index(self, img):
        imgDateStr = img.date().format()
        groupIndex = imgDateStr.slice(0, self.cfg.groupLevel)  # 2017 - 07 - 23T14:11:22(len: 19)

        Date = (imgDateStr.slice(0, self.cfg.labelShowLevel)
                .replace('-', '').replace('-', '').replace(':', '').replace(':', ''))

        imgLabel = (Date).cat(f"_{self.sat_name}")

        return img.setMulti({
            'GROUP_INDEX': groupIndex,
            'SAT_NAME': self.sat_name,
            'IMG_LABEL': imgLabel
        })

    def add_roi_cloud_rate(self, img):
        intersec = self.roi.intersection(img.geometry(), maxError=1)
        roi_area = compuate_area_from_image(self.roi_img.gt(0), intersec)
        cloud_img = img.select('cloud').eq(0)
        cloud_area = compuate_area_from_image(cloud_img, intersec)
        roi_cloud_rate = cloud_area.divide(roi_area).multiply(100)
        return img.setMulti({'ROI_CLOUD_RATE': roi_cloud_rate})

    # "group by date
    def group_MSI_ImgCol(self, imgcollection, multiSensorGroupFlag=False):
        imgCol = imgcollection.sort("system:time_start")
        # imgCol = imgCol_sort.map(self.set_group_index)

        d = imgCol.distinct(['GROUP_INDEX'])
        di = ee.ImageCollection(d)

        # Join collection to itself grouped by date
        date_eq_filter = ee.Filter.And(
            ee.Filter.equals(leftField='GROUP_INDEX', rightField='GROUP_INDEX')
            , ee.Filter.equals(leftField='SAT_NAME', rightField='SAT_NAME'))

        if (multiSensorGroupFlag):  # if it is allowed to group data from multiple sensor.
            date_eq_filter = ee.Filter.equals(leftField='GROUP_INDEX', rightField='GROUP_INDEX')

        saveall = ee.Join.saveAll("to_mosaic")
        j = saveall.apply(di, imgCol, date_eq_filter)
        ji = ee.ImageCollection(j)

        # original_proj = ee.Image(ji.first()).select(0).projection()

        def mosaicImageBydate(img):
            imgCol2mosaic = ee.ImageCollection.fromImages(img.get('to_mosaic'))
            firstImgGeom = imgCol2mosaic.first().geometry()
            mosaicGeom = ee.Geometry(imgCol2mosaic.iterate(self.unionGeomFun, firstImgGeom))
            mosaiced = imgCol2mosaic.mosaic().copyProperties(img, img.propertyNames())
            return ee.Image(mosaiced).set("system:footprint", mosaicGeom)  # lost

        imgcollection_grouped = ji.map(mosaicImageBydate)
        return ee.ImageCollection(imgcollection_grouped.copyProperties(imgCol, imgCol.propertyNames()))
    
    
class LANDSAT8(MSI):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.cfg = cfg
        # self.L8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA") # TOA Reflectance
        self.L8 = ee.ImageCollection(cfg.L8) # Surface Reflectance
        self.sat_name = 'L8'
    
    def query_l8_wo_processing(self):
        self.L8_filtered = (self.L8.filterBounds(self.roi)
                    .filterDate(self.checkStartDate, self.checkEndDate)
                    .filter(ee.Filter.lt('CLOUD_COVER_LAND', self.cfg.cloudLevel))
                    .map(self.set_group_index)
                )

        self.L8_grouped = (
                    self.group_MSI_ImgCol(self.L8_filtered)
                    .map(self.L8_bandRename)
                    .map(self.updateCloudMaskL8)
                    .map(self.set_group_index)
                )

        logger.info(f"L8_grouped: {self.L8_grouped.size().getInfo()}")
                        

    def __call__(self):
        
        L8_filtered = (self.L8.filterBounds(self.roi)
                    .filterDate(self.checkStartDate, self.checkEndDate)
                    .filter(ee.Filter.lt('CLOUD_COVER_LAND', self.cfg.cloudLevel))
                    .map(self.set_group_index)
                    )

        self.L8_grouped = ee.ImageCollection(self.group_MSI_ImgCol(L8_filtered)
                                        .map(self.L8_bandRename)
                                        .map(self.updateCloudMaskL8)
                                        # .map(self.set_group_index)
                                    )
        
    def L8_bandRename(self, img):
        toBandNameList = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2', 'PAN', 'cloud']
        # toBandNameList = ['B2', 'B3', 'B4', 'NIR', 'B11', 'B12', 'cloud']
        cloudBand = 'BQA' if 'TOA' in self.cfg.L8 else 'pixel_qa'
        return (img.select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', cloudBand])
                .rename(toBandNameList).copyProperties(img, img.propertyNames()))

    # def mask_L8_clouds(self, img):
    #     return img.updateMask(self.updateCloudMaskL8(img).select('cloud'))

    # def updateCloudMaskL8(self, img):
    #     qa = img.select('cloud')  # BQA
    #     mask = qa.bitwiseAnd(1 << 4).eq(0)
    #     return img.addBands(mask, overwrite=True) # 0 for cloud, 1 for clear

    # https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C01_T1_SR
    def updateCloudMaskL8(self, img):
        # Bits 3 and 5 are cloud shadow and cloud, respectively.
        cloudShadowBitMask = (1 << 3)
        cloudsBitMask = (1 << 5)
        # Get the pixel QA band.
        qa = img.select('cloud')
        # Both flags should be set to zero, indicating clear conditions.
        mask = (qa.bitwiseAnd(cloudShadowBitMask).eq(0)
                    .And(qa.bitwiseAnd(cloudsBitMask).eq(0))) # 0 for cloud, 1 for clear
        return img.addBands(mask.rename('cloud'), overwrite=True) # 0 for cloud, 1 for clear


class SENTINEL2(MSI):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.cfg = cfg
        self.S2 = ee.ImageCollection(cfg.S2) # TOA Reflectance scaled by 1e4
        # self.S2 = ee.ImageCollection("COPERNICUS/S2_SR") # Surface Reflectance scaled by 1e4
        self.sat_name = 'S2'

    def query_s2_wo_processing(self):
        self.S2_filtered = ee.ImageCollection(self.S2.filterBounds(self.roi)
                        .filterDate(self.checkStartDate, self.checkEndDate)
                        .filter(ee.Filter.lt('CLOUD_COVERAGE_ASSESSMENT', self.cfg.cloudLevel))
                        .map(self.set_group_index)
                    )

        """ get local crs before imgCol grouping"""
        # self.cfg.fireEvent.crs = self.S2_filtered.first().select(0).projection().crs().getInfo()
        # logger.info(f"CRS -> {self.cfg.fireEvent.crs}")

        self.S2_grouped = (self.group_MSI_ImgCol(self.S2_filtered)
                        .map(self.S2_bandScale)
                        .map(self.S2_bandRename)
                        .map(self.updateCloudMaskS2)
                        # .map(mask_S2_clouds)
                )
        logger.info(f"S2_grouped: {self.S2_grouped.size().getInfo()}")

    def __call__(self):
        
        S2_filtered = ee.ImageCollection(self.S2.filterBounds(self.roi)
                        .filterDate(self.checkStartDate, self.checkEndDate)
                        .filter(ee.Filter.lt('CLOUD_COVERAGE_ASSESSMENT', self.cfg.cloudLevel))
                        .map(self.set_group_index)
                    )

        self.S2_SCL = self.group_MSI_ImgCol(S2_filtered)
        self.S2_grouped = (self.S2_SCL
                        .map(self.S2_bandScale)
                        .map(self.S2_bandRename)
                        .map(self.updateCloudMaskS2)
                        # .map(mask_S2_clouds)
                )

    
    """ Sentinel-2 """
    def S2_bandRename(self, img):
        toBandNameList = ['B', 'G', 'R', 'NIR', 'PAN', 'SWIR1', 'SWIR2', 'cloud']
        return (img.select(['B2', 'B3', 'B4', 'B8A', 'B8', 'B11', 'B12', 'QA60'])
                    # .addBands(img.select('SCL')) # Scene Classification Layer (SCL)
                    .rename(toBandNameList).copyProperties(img, img.propertyNames()))


    # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
    def updateCloudMaskS2(self, img): 
        qa = img.select('cloud')  # QA60
        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11
        mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
            qa.bitwiseAnd(cirrusBitMask).eq(0))
        return img.addBands(mask, overwrite=True)


    # linearly rescale all images from [0, 10'000] to [0, 1]
    def S2_bandScale(self, img):
        return (ee.Image(img).select('B.*').divide(10000).clamp(0,1)
                .addBands(img.select('QA60'))  # keep BQA and cloud bands
                # .addBands(img.select('SCL'))
                .copyProperties(img, img.propertyNames()))


    def mask_S2_clouds(self, img):
        return img.updateMask(self.updateCloudMaskS2(img).select('cloud'))

   