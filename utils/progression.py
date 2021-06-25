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
        if len(list(cfg.fireEvent.roi)) == 4:
            self.cfg.fireEvent.roi = ee.Geometry.Rectangle(cfg.fireEvent.roi)

        if len(list(cfg.fireEvent.roi)) == 5:
            self.cfg.fireEvent.roi = ee.Geometry.Polygon(cfg.fireEvent.roi)

        # MODIS [+ Rainfall?]
        self.modis = ee.ImageCollection("MODIS/006/MCD64A1")
        self.modisBurnDate = self.modis.filterDate(ee.Date(self.cfg.fireEvent.startDate).advance(-1, 'month'),\
                ee.Date(self.cfg.fireEvent.endDate).advance(1, 'month')).select('BurnDate')\
                .mosaic().set("IMG_LABEL", 'modisPrgMap')

        # NLCD + BIOME + MTBS
        nlcd = ee.Image("USGS/NLCD_RELEASES/2016_REL/2016_AK").select('landcover').rename('nlcd').set("IMG_LABEL", 'NLCD')

        ecoRegions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
        biome = ecoRegions.reduceToImage(['BIOME_NUM'], ee.Reducer.first()).rename("BIOME_NUM").set("IMG_LABEL", 'BIOME')

        mtbs_url = f"gs://eo4wildfire/MTBS_AK_COG/{self.cfg.fireEvent.mtbs}"
        mtbs = ee.Image.loadGeoTIFF(mtbs_url).unmask().rename('mtbs').set("IMG_LABEL", 'MTBS')

        mtbs_dnbr_url = f"gs://eo4wildfire/MTBS_AK_COG/{self.cfg.fireEvent.mtbs[:-5]}.tif"
        dnbr = ee.Image.loadGeoTIFF(mtbs_dnbr_url).unmask().rename('dnbr').set("IMG_LABEL", 'dNBR')
        
        # if True: # if use MTBS Boundary as ROI
        #     self.cfg.fireEvent.roi = mtbs.gte(0).reduceToVectors().geometry()

        self.eco_bio_mtbs_imgCol = ee.ImageCollection([nlcd, biome, mtbs, dnbr])

    def __call__(self):

        self.preFilter = ee.Filter.date(ee.Date(self.cfg.fireEvent.startDate).advance(-0.25, 'month'), self.cfg.fireEvent.startDate)
        self.postFilter = ee.Filter.date(self.cfg.fireEvent.endDate, ee.Date(self.cfg.fireEvent.endDate).advance(0.25, 'month'))
        
        """ 
        ///////////////////////////////////////////////////////////////////////////////////////////
        ///////////////////////////////////// Query MSI DATA ////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////////////////////
        """
        if self.cfg.msiQueryFlag:
            msi = MSI(self.cfg)
            # msi.query_and_processing()
            msi.query_wo_processing()
            msi.set_cornor_points(buffer_size=-1e4) # -2000

            pntsFilter = ee.Filter.And(
                    ee.Filter.geometry(msi.btmLeft),
                    ee.Filter.geometry(msi.btmRight),
                    ee.Filter.geometry(msi.topRight),
                    # ee.Filter.geometry(msi.topLeft)
                )

            self.msi = msi
            self.msiImgCol = (msi.msiImgCol
                    .filterDate(ee.Date(msi.fireStartDate).advance(-self.cfg.numOfMonths, 'month'),\
                            ee.Date(msi.fireEndDate).advance(self.cfg.numOfMonths, 'month')) # .advance(10, 'day')
                    .filter(pntsFilter)
                    .filter(ee.Filter.lte("ROI_CLOUD_RATE", self.cfg.roi_cloud_rate))
                )

            # self.msi.printList(self.msiImgCol.aggregate_array('IMG_LABEL').sort().getInfo(), "msiImgCol to Download")
            
        """ 
        ///////////////////////////////////////////////////////////////////////////////////////////
        //////////////////////////////////// Query SAR DATA ////////////////////////////////////
        ///////////////////////////////////////////////////////////////////////////////////////////
        """
        if self.cfg.sarQueryFlag:
            """--------------------- SAR Data Query ------------------"""
            print(f"==> {self.cfg.fireEvent.crs}")
            sar = SAR(self.cfg)
            # sar.query_and_processing()
            sar.query_wo_processing()
            sar.set_cornor_points(buffer_size=-1e4) # -2000

            pntsFilter = ee.Filter.And(
                    ee.Filter.geometry(sar.btmLeft),
                    ee.Filter.geometry(sar.btmRight),
                    ee.Filter.geometry(sar.topRight),
                    # ee.Filter.geometry(sar.topLeft)
                )

            self.sar = sar
            self.sarImgCol = (sar.sarImgCol
                    .filterDate(ee.Date(sar.fireStartDate).advance(-self.cfg.numOfMonths, 'month'),\
                        ee.Date(sar.fireEndDate).advance(self.cfg.numOfMonths, 'month')) # .advance(10, 'day')
                    .filter(pntsFilter)
                )

            # self.sar.printList(self.sarImgCol.aggregate_array('IMG_LABEL').sort().getInfo(), "sarImgCol to Download")


    """ 
    ///////////////////////////////////////////////////////////////////////////////////////////
    //////////////////////////////////// Functions to call ////////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////////////
    """
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

    """ 
    ///////////////////////////////////////////////////////////////////////////////////////////
    //////////////////////////////// Export Progression to Local //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////////////
    """
    def export_progression_to_local(self, scale=20):
        ''' Exporting data to local has a limitation on data size '''
        print(f"Local folder: {self.cfg.savePath}")

        if self.cfg.msiQueryFlag:
            if self.cfg.Export.MSI_PRE_POST_ONLY:
                msiImgCol = self.msiImgCol.filter(ee.Filter.Or(self.preFilter, self.postFilter))
            else: msiImgCol = self.msiImgCol
        
        if self.cfg.sarQueryFlag:
            if self.cfg.Export.SAR_PRE_POST_ONLY:
                sarImgCol = self.sarImgCol.filter(ee.Filter.Or(self.preFilter, self.postFilter))
            else: sarImgCol = self.sarImgCol

        """--------------------- Data AutoExport ------------------"""
        self.cfg.Export.MSI = self.cfg.msiQueryFlag and self.cfg.Export.MSI
        self.cfg.Export.dNBR = self.cfg.msiQueryFlag and self.cfg.Export.dNBR

        self.cfg.Export.SAR = self.cfg.sarQueryFlag and self.cfg.Export.SAR
        self.cfg.Export.kMap = self.cfg.sarQueryFlag and self.cfg.Export.kMap

        """ MSI """
        if self.cfg.Export.MSI:
            self.msi.batch_imgCol_download(
                imgCol=msiImgCol, 
                scale=scale,
                pathKeyWord = 'MSI', bands4download=list(self.cfg.BANDS.MSI), 
                toRGBflag=True, stretchFlag=True, rgbVisBands=list(self.cfg.BANDS.MSI_VIS))
        
        """ dNBR """
        if self.cfg.Export.dNBR:
            self.msi.batch_imgCol_download(
                imgCol=msiImgCol, 
                scale=scale,
                pathKeyWord = 'dNBR', bands4download=list(self.cfg.BANDS.dNBR), 
                toRGBflag=False, stretchFlag=True, rgbVisBands=list(self.cfg.BANDS.dNBR_VIS))

        ''' SAR kMap '''
        def to8bit_SAR(img): 
            return (img.select(list(self.cfg.BANDS.SAR))
                    .multiply(255).toUint8().float().divide(255)
                    .copyProperties(img, img.propertyNames()))

        if self.cfg.Export.SAR:
            self.sar.batch_imgCol_download(
                imgCol=sarImgCol.map(to8bit_SAR), #
                scale=scale,
                pathKeyWord='SAR', bands4download=list(self.cfg.BANDS.SAR), 
                toRGBflag=True, stretchFlag=True, rgbVisBands=list(self.cfg.BANDS.SAR_VIS))
        
        ''' SAR kMap '''
        if self.cfg.Export.kMap and self.cfg.sar_logRt_Flag:
            self.sar.batch_imgCol_download(
                imgCol=sarImgCol, #.map(add_firename), 
                scale=scale,
                pathKeyWord='kMap', bands4download=list(self.cfg.BANDS.kMap), 
                toRGBflag=True, stretchFlag=True, rgbVisBands=list(self.cfg.BANDS.kMap_VIS))

        # if msi was not queried, then use sar instead
        if self.cfg.msiQueryFlag: eo = self.msi
        if (not self.cfg.msiQueryFlag) and self.cfg.sarQueryFlag: eo = self.sar

        ''' Cloud Cover + Land Cover + PolyMap ''' 
        if self.cfg.Export.LC:
            eo.batch_imgCol_download(
                imgCol=ee.ImageCollection([eo.landCover]).merge(self.eco_bio_mtbs_imgCol), # fireEvent.polyMap
                scale=scale,
                pathKeyWord = 'REFMASK', bands4download=[], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        if self.cfg.Export.polyMap and ('polyMap' in self.cfg.fireEvent.keys()):
            eo.batch_imgCol_download(
                imgCol=ee.ImageCollection([self.cfg.fireEvent.polyMap]), # fireEvent.polyMap
                scale=scale,
                pathKeyWord = 'REFMASK', bands4download=[], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        """ MODIS """
        if self.cfg.Export.MODIS:
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.batch_imgCol_download(
                imgCol=ee.ImageCollection([self.modisBurnDate]), #.map(self.add_firename),        
                scale=scale,
                pathKeyWord = 'REFMASK', bands4download=[], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        """ Binarize dNBR/dNBR1 """
        if self.cfg.Export.dNBR_BIN:
            if 'SR' in self.cfg.S2: dNBR_imgCol = msiImgCol.map(self.bin_dNBR)
            else: dNBR_imgCol = msiImgCol.map(self.bin_dNBR1)
            self.msi.batch_imgCol_download(
                imgCol=dNBR_imgCol, 
                scale=scale,
                pathKeyWord = 'dNBR1_BIN', bands4download=[], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=[])

        """ kMap BIN """
        if self.cfg.Export.kMap_BIN:
            self.sar.batch_imgCol_download(
                imgCol=sarImgCol.select(['kCR', 'kVH', 'kVV']).gt(1), 
                scale=scale,
                pathKeyWord = 'kMapBIN', bands4download=['kCR', 'kVH', 'kVV'], 
                toRGBflag=False, stretchFlag=True, rgbVisBands=['kCR', 'kVH', 'kVV'])

    """ 
    ///////////////////////////////////////////////////////////////////////////////////////////
    //////////////////////////////// Export Progression to Drive //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////////////
    """
    def export_progression_to_Drive(self, scale=20):
        print(f"Drive/Cloud folder: {self.cfg.driveFolder}")

        if self.cfg.msiQueryFlag:
            if self.cfg.Export.MSI_PRE_POST_ONLY:
                msiImgCol = self.msiImgCol.filter(ee.Filter.Or(self.preFilter, self.postFilter))
            else: msiImgCol = self.msiImgCol
        
        if self.cfg.sarQueryFlag:
            if self.cfg.Export.SAR_PRE_POST_ONLY:
                sarImgCol = self.sarImgCol.filter(ee.Filter.Or(self.preFilter, self.postFilter))
            else: sarImgCol = self.sarImgCol

        """ --------------------- Data AutoExport ------------------ """
        self.cfg.Export.MSI = self.cfg.msiQueryFlag and self.cfg.Export.MSI
        self.cfg.Export.dNBR = self.cfg.msiQueryFlag and self.cfg.Export.dNBR

        self.cfg.Export.SAR = self.cfg.sarQueryFlag and self.cfg.Export.SAR
        self.cfg.Export.kMap = self.cfg.sarQueryFlag and self.cfg.Export.kMap
        
        # scale = 20
        """ MSI rgb """
        if self.cfg.Export.MSI:
            self.msi.export_imgCol_to_Drive(
                imgCol=msiImgCol, 
                bandList=list(self.cfg.BANDS.MSI), 
                scale=scale,
                filePerBand=True)

        """ dNBR """
        if self.cfg.Export.dNBR:
            self.msi.export_imgCol_to_Drive(
                imgCol=msiImgCol, 
                bandList=list(self.cfg.BANDS.dNBR), 
                scale=scale,
                filePerBand=True)

        """ SAR """
        if self.cfg.Export.SAR:
            self.sar.export_imgCol_to_Drive(
                imgCol=sarImgCol, 
                bandList=list(self.cfg.BANDS.SAR), 
                scale=scale,
                filePerBand=True)

        """ SAR kMap """
        if self.cfg.Export.kMap and self.cfg.sar_logRt_Flag:
            self.sar.export_imgCol_to_Drive(
                imgCol=sarImgCol, 
                bandList=list(self.cfg.BANDS.kMap), 
                scale=scale,
                filePerBand=True)

        # if msi was not queried, then use sar instead
        if self.cfg.msiQueryFlag: eo = self.msi
        if (not self.cfg.msiQuery) and self.cfg.sarQueryFlag: eo = self.sar

        """ Land Cover """
        if self.cfg.Export.LC:
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.export_imgCol_to_Drive(
                imgCol=ee.ImageCollection([eo.landCover]).merge(self.eco_bio_mtbs_imgCol),  #.map(self.add_firename)
                bandList=[], 
                scale=scale,
                filePerBand=False)

        """ PolyMap """
        if self.cfg.Export.polyMap and ('polyMap' in self.cfg.fireEvent.keys()):
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.export_imgCol_to_Drive(
                imgCol=ee.ImageCollection([self.cfg.fireEvent.polyMap]), #.map(self.add_firename),        
                bandList=[], 
                scale=scale,
                filePerBand=False)

        """ MODIS """
        if self.cfg.Export.MODIS:
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.export_imgCol_to_Drive(
                imgCol=ee.ImageCollection([self.modisBurnDate]), #.map(self.add_firename),        
                bandList=[], 
                scale=scale,
                filePerBand=False)
    
    """ 
    ///////////////////////////////////////////////////////////////////////////////////////////
    //////////////////////////////// Export Progression to Cloud //////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////////////
    """
    def export_progression_to_CloudStorage(self, scale=20, filePerBand=False):
        print(f"BUCKET: {self.cfg.BUCKET}")
        print(f"Drive/Cloud folder: {self.cfg.driveFolder}")
        if self.cfg.msiQueryFlag:
            if self.cfg.Export.MSI_PRE_POST_ONLY:
                msiImgCol = self.msiImgCol.filter(ee.Filter.Or(self.preFilter, self.postFilter))
            else: msiImgCol = self.msiImgCol
        
        if self.cfg.sarQueryFlag:
            if self.cfg.Export.SAR_PRE_POST_ONLY:
                sarImgCol = self.sarImgCol.filter(ee.Filter.Or(self.preFilter, self.postFilter))
            else: sarImgCol = self.sarImgCol


        """ --------------------- Data AutoExport ------------------ """
        self.cfg.Export.MSI = self.cfg.msiQueryFlag and self.cfg.Export.MSI
        self.cfg.Export.dNBR = self.cfg.msiQueryFlag and self.cfg.Export.dNBR

        self.cfg.Export.SAR = self.cfg.sarQueryFlag and self.cfg.Export.SAR
        self.cfg.Export.kMap = self.cfg.sarQueryFlag and self.cfg.Export.kMap
        
        # scale = 20
        """ MSI rgb """
        if self.cfg.Export.MSI:
            self.msi.export_imgCol_to_CloudStorage(
                imgCol=msiImgCol, 
                bandList=list(self.cfg.BANDS.MSI), 
                scale=scale,
                filePerBand=filePerBand)

        """ dNBR """
        if self.cfg.Export.dNBR:
            self.msi.export_imgCol_to_CloudStorage(
                imgCol=msiImgCol, 
                bandList=list(self.cfg.BANDS.dNBR), 
                scale=scale,
                filePerBand=filePerBand)

        """ SAR """
        if self.cfg.Export.SAR:
            self.sar.export_imgCol_to_CloudStorage(
                imgCol=sarImgCol, 
                bandList=list(self.cfg.BANDS.SAR), 
                scale=scale,
                filePerBand=filePerBand)

        """ SAR kMap """
        if self.cfg.Export.kMap and self.cfg.sar_logRt_Flag:
            self.sar.export_imgCol_to_CloudStorage(
                imgCol=sarImgCol, 
                bandList=list(self.cfg.BANDS.kMap), 
                scale=scale,
                filePerBand=filePerBand)

        # if msi was not queried, then use sar instead
        if self.cfg.msiQueryFlag: eo = self.msi
        if (not self.cfg.msiQueryFlag) and self.cfg.sarQueryFlag: eo = self.sar

        """ Land Cover """
        if self.cfg.Export.LC:
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.export_imgCol_to_CloudStorage(
                imgCol=ee.ImageCollection([eo.landCover]).merge(self.eco_bio_mtbs_imgCol), #.map(self.add_firename),        
                bandList=[], 
                scale=scale
            )

        """ PolyMap """
        if self.cfg.Export.polyMap and ('polyMap' in self.cfg.fireEvent.keys()):
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.export_imgCol_to_CloudStorage(
                imgCol=ee.ImageCollection([self.cfg.fireEvent.polyMap]), #.map(self.add_firename),        
                bandList=[], 
                scale=10
            )

        """ MODIS """
        if self.cfg.Export.MODIS:
            eo.driveFolder = f"{self.cfg.driveFolder}/REFMASK"
            eo.export_imgCol_to_CloudStorage(
                imgCol=ee.ImageCollection([self.modisBurnDate]), #.map(self.add_firename),        
                bandList=[], 
                scale=scale
            )
        

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
