import ee
from eo_class.SAR import SAR
from eo_class.MSI import MSI
from easydict import EasyDict as edict
from prettyprinter import pprint

import logging
logger = logging.getLogger(__name__)

class PROGRESSION:
    def __init__(self, cfg):
        self.cfg = cfg

    def __call__(self):
        
        if self.cfg.msiQueryFlag:
            """-------------------- MSI Data Query ----------------"""
            msi = MSI(self.cfg)
            msi = msi
            msi.query_and_processing()
            # msi.query_wo_processing()
            msi.set_cornor_points(buffer_size=-2000)

            pntsFilter = ee.Filter.And(
                    ee.Filter.geometry(msi.btmLeft),
                    ee.Filter.geometry(msi.btmRight),
                    ee.Filter.geometry(msi.topRight),
                    ee.Filter.geometry(msi.topLeft)
                )

            self.msi = msi
            self.msiImgCol = (msi.msiImgCol
                    .filterDate(msi.fireStartDate, ee.Date(msi.fireEndDate).advance(1, 'month'))
                    .filter(pntsFilter)
                    .filter(ee.Filter.lte("ROI_CLOUD_RATE", self.cfg.roi_cloud_rate))
                )

            self.msi.printList(self.msiImgCol.aggregate_array('IMG_LABEL').sort().getInfo(), "msiImgCol to Download")
            

        if self.cfg.sarQueryFlag:
            """--------------------- SAR Data Query ------------------"""
            print(f"==> {self.cfg.fireEvent.crs}")
            sar = SAR(self.cfg)
            sar.query_and_processing()
            sar.set_cornor_points(buffer_size=-2000)
            # sar.query_wo_processing()

            pntsFilter = ee.Filter.And(
                    ee.Filter.geometry(sar.btmLeft),
                    ee.Filter.geometry(sar.btmRight),
                    ee.Filter.geometry(sar.topRight),
                    ee.Filter.geometry(sar.topLeft)
                )

            self.sar = sar
            logger.info(f"CRS -> {self.sar.cfg.fireEvent.crs}")

            self.sarImgCol = (sar.sarImgCol
                    .filterDate(sar.fireEndDate, ee.Date(sar.fireEndDate).advance(1, 'month')) # .advance(10, 'day')
                    .filter(pntsFilter)
                )

            self.sar.printList(self.sarImgCol.aggregate_array('IMG_LABEL').sort().getInfo(), "sarImgCol to Download")

    
    def add_spatialMeanStd(self, img):
        spatial_mean = img.reduceRegion(
                                reducer=ee.Reducer.mean(), 
                                geometry=self.cfg.fireEvent.roi, 
                                scale = 20,
                                maxPixels = 1e10,
                                tileScale = 4
                            ).toImage()

        # spatial_stdDev = img.reduceRegion(
        #                         reducer=ee.Reducer.stdDev(), 
        #                         geometry=self.cfg.fireEvent.roi, 
        #                         scale = 20,
        #                         maxPixels = 1e10,
        #                         tileScale = 4
        #                     ).toImage()

        return (img.subtract(spatial_mean).gt(0)
                .multiply(255).toUint8().float().divide(255)
                .copyProperties(img, img.propertyNames()))
    
    """ Functions to call """
    def bin_dNBR(self, img): return img.select("dNBR").gt(0.1).rename('dNBR')\
                                .setMulti({'IMG_LABEL': img.get('IMG_LABEL')})

    def bin_dNBR1(self, img): return img.select("dNBR1").gt(0.2).rename('dNBR1')\
                                .setMulti({'IMG_LABEL': img.get('IMG_LABEL')})

    def bin_kMap(self, img):  
        binMap = img.select(['kCR', 'kVH', 'kVV']).abs().gt(1)
        return binMap.addBands(binMap.expression("b('kCR')+b('kVH')+b('kVV')").gt(0).rename('mrg'))\
        .setMulti({'IMG_LABEL': img.get('IMG_LABEL')})

    def add_firename(self, img):
        return img.setMulti({"IMG_LABEL": ee.String(self.cfg.fireEvent.name).cat('_').cat(img.get("IMG_LABEL"))})

    """ To 8-bit """
    def to8bitV1(self, img): 
        mmax = 1
        return (img.clamp(0, mmax).divide(mmax).multiply(255).toUint8()
                    .toFloat().divide(255).multiply(mmax)
                    .setMulti({"IMG_LABEL": img.get("IMG_LABEL")})
        )

    ''' Mean + StdDev '''
    def export_mean_std(self, scale=20):
        sarMeanDict = self.sar.sarMeanDict
        sarStdDict = self.sar.sarStdDict

        meanImgCol = ee.ImageCollection([])
        stdImgCol = ee.ImageCollection([])
        for key in sarMeanDict.keys():
            sarMeanImg = ee.Image(sarMeanDict[key].setMulti({"IMG_LABEL": ee.String('MEAN_').cat(key)}))
            meanImgCol = meanImgCol.merge(ee.ImageCollection([sarMeanImg]))

            sarStdImg = ee.Image(sarStdDict[key].setMulti({"IMG_LABEL": ee.String('STD_').cat(key)}))
            stdImgCol = stdImgCol.merge(ee.ImageCollection([sarStdImg]))

        self.sar.batch_imgCol_download(
            imgCol=meanImgCol.select(['CR_mean', 'VH_mean', 'VV_mean']).map(self.to8bitV1), 
            scale=scale,
            pathKeyWord = 'MEANSTD', bands4download=['CR_mean', 'VH_mean', 'VV_mean'], 
            toRGBflag=True, stretchFlag=True, rgbVisBands=['CR_mean', 'VH_mean', 'VV_mean'])

        self.sar.batch_imgCol_download(
            imgCol=stdImgCol.select(['CR_std', 'VH_std', 'VV_std']).map(self.to8bitV1), 
            scale=scale,
            pathKeyWord = 'MEANSTD', bands4download=['CR_std', 'VH_std', 'VV_std'], 
            toRGBflag=True, stretchFlag=True, rgbVisBands=['CR_std', 'VH_std', 'VV_std'])

    def export_SCL_to_local(self, scale=20):
        SCL_imgLabelList = self.msiImgCol.aggregate_array('IMG_LABEL').getInfo()
        SCL_imgCol = self.msi.S2_SCL.filter(ee.Filter.inList("IMG_LABEL", SCL_imgLabelList))

        self.msi.batch_imgCol_download(
            imgCol=SCL_imgCol,
            scale=scale,
            pathKeyWord = 'LC', bands4download=['SCL'], 
            toRGBflag=False, stretchFlag=True, rgbVisBands=[])


    ''' Exporting data to local has a limitation on data size '''
    def export_progression_to_local(self, scale=20):

        if self.cfg.msiQueryFlag:    
            msi = self.msi
            msiImgCol = self.msiImgCol
            print(f"local folder: {msi.rootPath}")
        
        if self.cfg.sarQueryFlag:
            sar = self.sar      
            sarImgCol = self.sarImgCol
            print(f"local folder: {sar.rootPath}")


        """--------------------- Data AutoExport ------------------"""

        ''' MSI rgb '''
        if self.cfg.Export.OptRGB:
            msi.batch_imgCol_download(
                imgCol=self.msiImgCol, 
                scale=scale,
                pathKeyWord = 'SWIR', bands4download=['SWIR2', 'NIR', 'R'], 
                toRGBflag=True, stretchFlag=True, rgbVisBands=['SWIR2', 'NIR', 'R'])
        
        """ dNBR """
        if self.cfg.Export.dNBR:
            msi.batch_imgCol_download(
                imgCol=self.msiImgCol, 
                scale=scale,
                pathKeyWord = 'dNBR1', bands4download=['dNBR1'], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        ''' SAR kMap '''
        def to8bit_SAR(img): 
            return (img.select(['CR', 'VH', 'VV'])
                    .multiply(255).toUint8().float().divide(255)
                    .copyProperties(img, img.propertyNames()))

        if self.cfg.Export.SAR:
            sar.batch_imgCol_download(
                imgCol=self.sarImgCol.map(to8bit_SAR), 
                scale=scale,
                pathKeyWord = 'SAR', bands4download=['CR', 'VH', 'VV'], 
                toRGBflag=True, stretchFlag=True, rgbVisBands=['CR', 'VH', 'VV'])
        
        ''' SAR kMap '''
        if self.cfg.Export.kMap:
            sar.batch_imgCol_download(
                imgCol=self.sarImgCol.map(add_firename), 
                scale=scale,
                pathKeyWord = 'kMap', bands4download=['kCR', 'kVH', 'kVV'], 
                toRGBflag=True, stretchFlag=True, rgbVisBands=['kCR', 'kVH', 'kVV'])


        ''' Cloud Cover + Land Cover + PolyMap '''  
        if self.cfg.Export.LC:
            msi.batch_imgCol_download(
                imgCol=ee.ImageCollection([self.msi.landCover, 
                                                self.cfg.fireEvent.polyMap]), # fireEvent.polyMap
                scale=scale,
                pathKeyWord = 'LC', bands4download=[], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        """ Binarize dNBR/dNBR1 """
        if self.cfg.Export.dNBR_BIN:
            if 'SR' in self.cfg.S2: dNBR_imgCol = msiImgCol.map(self.bin_dNBR)
            else: dNBR_imgCol = msiImgCol.map(self.bin_dNBR1)
            msi.batch_imgCol_download(
                imgCol=dNBR_imgCol, 
                scale=scale,
                pathKeyWord = 'dNBR1_BIN', bands4download=[], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        """ kMap BIN """
        if self.cfg.Export.kMap_BIN:
            sar.batch_imgCol_download(
                imgCol=sarImgCol.select(['kCR', 'kVH', 'kVV']).gt(1), 
                scale=scale,
                pathKeyWord = 'kMapBIN', bands4download=['kCR', 'kVH', 'kVV'], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=['kCR', 'kVH', 'kVV'])



    def export_progression_to_CloudStorage(self, scale=20):
        if self.cfg.msiQueryFlag:    
            msi = self.msi
            msiImgCol = self.msiImgCol
            print(f"Drive/Cloud folder: {msi.rootPath}")
        
        if self.cfg.sarQueryFlag:
            sar = self.sar      
            sarImgCol = self.sarImgCol
            print(f"Drive/Cloud folder: {sar.rootPath}")

        # cfg = self.cfg

        """--------------------- Data AutoExport ------------------"""
        self.cfg.Export.OptRGB = self.cfg.msiQueryFlag and self.cfg.Export.OptRGB
        self.cfg.Export.dNBR = self.cfg.msiQueryFlag and self.cfg.Export.dNBR
        
        # scale = 20
        """ MSI rgb """
        if self.cfg.Export.OptRGB:
            msi.export_imgCol_to_CloudStorage(
                imgCol=msiImgCol, 
                bandList=['SWIR2', 'NIR', 'SWIR1'], 
                scale=scale,
                filePerBand=True)

        """ dNBR """
        if self.cfg.Export.dNBR:
            msi.export_imgCol_to_CloudStorage(
                imgCol=msiImgCol, 
                bandList=['dNBR1'], 
                scale=scale,
                filePerBand=True)

        """ Land Cover """
        if self.cfg.Export.LC:
            msi.export_imgCol_to_CloudStorage(
                imgCol=ee.ImageCollection([msi.landCover, 
                            self.cfg.fireEvent.polyMap]).map(self.add_firename),        
                bandList=[], 
                scale=scale,
                filePerBand=True)


        """ SAR """
        if self.cfg.Export.SAR:
            sar.export_imgCol_to_CloudStorage(
                imgCol=sarImgCol, 
                bandList=['CR', 'VH', 'VV'], 
                scale=scale,
                filePerBand=True)

        """ SAR kMap """
        if self.cfg.Export.kMap:
            sar.export_imgCol_to_CloudStorage(
                imgCol=sarImgCol, 
                bandList=['kCR', 'kVH', 'kVV'], 
                scale=scale,
                filePerBand=True)
        
        

        # ''' Cloud Cover + Land Cover + PolyMap '''
        # # SCL_imgLabelList = msiImgCol.aggregate_array('IMG_LABEL').getInfo()
        # # SCL_imgCol = msi.S2_SCL.filter(ee.Filter.inList("IMG_LABEL", SCL_imgLabelList))
        # # msi.export_imgCol_to_CloudStorage(
        # #     imgCol=SCL_imgCol.select('SCL')\
        # #             .merge(ee.ImageCollection([msi.landCover, fireEvent.polyMap])),        
        # #     bandList=[], 
        # #     scale=20,
        # #     filePerBand=True)

        # """ Binarization """
        # msi.driveFolder = msi.driveFolder + "_OptREF"
        # sar.driveFolder = sar.driveFolder + "_SARREF"   
        # msi.export_imgCol_to_CloudStorage(
        #     imgCol=msiImgCol.map(self.bin_dNBR), 
        #     bandList=[], 
        #     scale=scale,
        #     filePerBand=True)

        # sar.export_imgCol_to_CloudStorage(
        #     imgCol=sarImgCol.map(self.bin_kMap), 
        #     bandList=['kCR', 'kVH', 'kVV'], 
        #     scale=scale,
        #     filePerBand=True)
