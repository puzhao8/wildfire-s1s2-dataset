import ee
import os
import numpy as np
import urllib.request as Request
import logging
import sys
import zipfile
from pathlib import Path
from imageio import imread, imsave

import logging
logger = logging.getLogger(__name__)

class EO_DATASET:
    def __init__(self, cfg):
        self.cfg = cfg

        self.rootPath = Path(cfg.savePath)
        self.G_kernel = ee.Kernel.gaussian(21)
        # self.export_scale = cfg.export_scale
        # self.fireName = cfg.fireEvent.fireName

        self.roi = cfg.fireEvent['roi']
        self.roiPoly = ee.FeatureCollection(self.roi).style(color='red', fillColor='#ff000000')
        self.fireStartDate = cfg.fireEvent['startDate']
        self.fireEndDate = cfg.fireEvent['endDate'] 

        self.myDrive = Path("/content/drive/My Drive")
        self.driveFolder = cfg.driveFolder
            
        self.checkHistoryFlag = cfg.checkHistoryFlag
        if self.checkHistoryFlag:
            self.checkStartDate = ee.Date(self.fireStartDate).advance(-2, 'month')
            self.checkEndDate = ee.Date(self.fireEndDate).advance(2, 'month')
        else:
            self.checkStartDate = ee.Date(self.fireStartDate)
            self.checkEndDate = ee.Date(self.fireEndDate)

        self.get_dem_and_landCover()

    def set_timeEnd_newdays(self, img):
        group_days = img.date().format().slice(0, 10)
        return img.set('system:time_end', group_days)

    def unionGeomFun(self, img, first):
        rightGeo = ee.Geometry(img.geometry())
        return ee.Geometry(first).union(rightGeo)

    def filt_morph(self, img):
        kernel_slope = ee.Kernel.gaussian(radius=2)
        kernel_slope2 = ee.Kernel.gaussian(radius=1)
        return ee.Image(img.focal_median(kernel=kernel_slope, iterations=1)
                .focal_max(kernel=kernel_slope2, iterations=1)
                .focal_min(kernel=kernel_slope2, iterations=1)
                .copyProperties(img, ['IMG_LABEL']))

    def imgConv(self, img):
        return img.convolve(self.G_kernel).float()

    # def printList(self, inList, markString=None):
    #     print("---------{}: {}----------".format(markString, len(inList)))
    #     for ele in inList:
    #         print(ele)
    #     print("---------------------\n")

    def printList(self, inList, markString=None):
        logger.info("---------{}: {}----------".format(markString, len(inList)))
        print("---------{}: {}----------".format(markString, len(inList)))
        
        for ele in inList:
            logger.info(ele)
            print(ele)
        logger.info("---------------------\n")
        print("---------------------\n")

    def set_cornor_points(self, buffer_size=0):
        ## ==> Point Filters <==
        pnt_roi = self.roi.buffer(buffer_size, ee.ErrorMargin(1)).bounds()
        coordList = ee.List(pnt_roi.coordinates().get(0))
        self.btmLeft = ee.Geometry.Point(coordList.get(0))
        self.btmRight = ee.Geometry.Point(coordList.get(1))
        self.topRight = ee.Geometry.Point(coordList.get(2))
        self.topLeft = ee.Geometry.Point(coordList.get(3))
        self.pntsFC = ee.FeatureCollection([self.btmLeft, self.btmRight, self.topRight, self.topLeft]).style(color="red")

        # if len(pntsList) > 0:
        self.pntsFilter = ee.Filter.And(
            ee.Filter.geometry(self.btmLeft),
            ee.Filter.geometry(self.btmRight),
            ee.Filter.geometry(self.topRight),
            ee.Filter.geometry(self.topLeft))

    def get_image_by_ImgLabel(self, imgCol, imgLabel):
        return imgCol.filter(ee.Filter.eq("IMG_LABEL", imgLabel)).first()

    
    """ DEM, water mask, and Land cover """
    def get_dem_and_landCover(self):
        """======================== DEM ============================"""
        # hansenImage = ee.Image('UMD/hansen/global_forest_change_2019_v1_7')
        # datamask = hansenImage.select('datamask')
        # waterMask0 = datamask.eq(1).rename('water')

        """ =============== Froest Land Cover 2017 ================= """
        landCover = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017")
        self.landCover = ee.Image(landCover.select("discrete_classification").rename('CGLS').setMulti({'IMG_LABEL': 'CGLS'}))#.eq(mainLandCover)
        waterMask0 = (self.landCover.neq(80).And(self.landCover.neq(200))).rename('water')

        dem_30m = ee.Image("USGS/SRTMGL1_003")
        dem = ee.Terrain.products(dem_30m)

        alos_dem = ee.Image("JAXA/ALOS/AW3D30_V1_1").select('AVE')
        terrain = ee.Terrain.products(alos_dem)
        slope = terrain.select("slope")
        aspect = terrain.select("aspect")
        hillshade = terrain.select("hillshade")

        ascMask = self.filt_morph(ee.Image(1).subtract(ee.Image(slope.gt(20)).multiply(hillshade.gt(180))).rename("ASC"))
        dscMask = self.filt_morph(ee.Image(1).subtract(ee.Image(slope.gt(20)).multiply(hillshade.lt(180))).rename("DSC"))
        
        # maskDict['ASC'] = ee.Image(waterMask.select('water').multiply(waterMask.select('ASC')))
        # maskDict['DSC'] = ee.Image(waterMask.select('water').multiply(waterMask.select('DSC')))

        self.waterMask = ee.Image((waterMask0.addBands(ascMask).addBands(dscMask)).setMulti({'IMG_LABEL': 'waterMask'}))


    def mask_water(self, img):
        """ mask water out """
        return ee.Image(img.multiply(self.waterMask.select('water')).copyProperties(img, img.propertyNames()))

    """
    /////////////////////////////////////////////////////////////////////////////////////
    //////////////////// Export Data to Drive or CloudStorage ///////////////////////////
    /////////////////////////////////////////////////////////////////////////////////////
    """
    """========================> Check Exporting Status <============================"""
    def check_export_task(self, task, imgName):
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

    """==============================> Export Data to Drive <================================="""
    def export_image_to_Drive(self, image, out_image_base, scale=20):
        """ Run the image export task.  Block until complete """
        task = ee.batch.Export.image.toDrive(
            image = image.toFloat(), 
            description = out_image_base, 
            folder = f"{self.driveFolder}",
            fileNamePrefix = out_image_base, 
            region = self.roi, #.getInfo()['coordinates'], 
            scale = scale, 
            crs = self.cfg.fireEvent.crs,
            fileFormat = 'GeoTIFF', 
            maxPixels = 1e10,
            formatOptions = { # Cloud-Optimized TIF
                "cloudOptimized": True
            }
        )
        task.start()
        self.check_export_task(task, out_image_base)

    def export_imgCol_to_Drive(self, imgCol, bandList, scale=20, filePerBand=False):
        """ export ImgCol to Drive """
        sizeOfImgCol = imgCol.size().getInfo()

        imgCol_List = imgCol.toList(sizeOfImgCol)
        for idx in range(sizeOfImgCol):
            image = ee.Image(imgCol_List.get(idx))
            out_image_base = f"{image.get('IMG_LABEL').getInfo()}"
            print(f"\n{out_image_base}")

            if filePerBand: 
                if len(bandList) > 0:
                    for band in bandList:
                        self.export_image_to_Drive(image.select(band), f"{out_image_base}.{band}", scale)
                else:
                    for band in image.bandNames().getInfo():
                        self.export_image_to_Drive(image.select(band), f"{out_image_base}.{band}", scale)

            else:
                if 0 == len(bandList): self.export_image_to_Drive(image, out_image_base, scale)
                if len(bandList) > 0: self.export_image_to_Drive(image.select(bandList), out_image_base, scale)
                

    """
    /////////////////////////////////////////////////////////////////////////////////////
    //////////////////////////// Export Data to Local Disk //////////////////////////////
    /////////////////////////////////////////////////////////////////////////////////////
    """
    def export_image_to_CloudStorage(self, image, out_image_base, scale=20):
        BUCKET=self.cfg.BUCKET
        
        """ Run the image export task.  Block until complete """
        task = ee.batch.Export.image.toCloudStorage(
            image = image.toFloat(), 
            description = out_image_base, 
            bucket = BUCKET, 
            # folder = f"{self.driveFolder}",
            fileNamePrefix = f"{self.driveFolder}/{out_image_base}", 
            region = self.roi, #.getInfo()['coordinates'], 
            scale = scale, 
            crs = self.cfg.fireEvent.crs,
            fileFormat = 'GeoTIFF', 
            maxPixels = 1e10,
            formatOptions = { # Cloud-Optimized TIF
                "cloudOptimized": True
            }
        )
        task.start()
        self.check_export_task(task, out_image_base)

    
    def export_imgCol_to_CloudStorage(self, imgCol, bandList, scale=20, filePerBand=False):
        """ export ImgCol to Drive """
        sizeOfImgCol = imgCol.size().getInfo()

        imgCol_List = imgCol.toList(sizeOfImgCol)
        for idx in range(sizeOfImgCol):
            image = ee.Image(imgCol_List.get(idx))
            out_image_base = f"{image.get('IMG_LABEL').getInfo()}"
            print(f"\n{out_image_base}")

            if not filePerBand:
                if len(bandList) > 0:
                    self.export_image_to_CloudStorage(image.select(bandList), out_image_base, scale)
                else:
                    self.export_image_to_CloudStorage(image, out_image_base, scale)
            else: # filePerBand
                for band in bandList:
                    self.export_image_to_CloudStorage(image.select(band), f"{out_image_base}.{band}", scale)

    

    """======================================> Export Data to Local <=========================================="""
    def batch_imgCol_download(self, imgCol, pathKeyWord, bands4download, 
                                toRGBflag=False, stretchFlag=True, rgbVisBands=[], scale=20):

        # self.rootPath = Path(self.cfg.savePath) / f"{self.cfg.fireEvent.name}_WildFire_SAR_MSI_{scale}m_{self.cfg.fireEvent.crs.replace(':', '_')}_{ee.Date(self.fireStartDate).format().split('-').getInfo()[0]}_MAD"
        epsg = self.cfg.fireEvent.crs.replace(":", "_")
        # self.rootPath = Path(self.cfg.savePath) / f"{self.cfg.fireEvent.name}_WildFire_SAR_MSI_{scale}m_{self.cfg.sarMasterMode}_{epsg}"
        self.rootPath = Path(self.cfg.savePath) / f"{self.cfg.fireEvent.name}"
        
        if "SR" in self.cfg.S2: self.rootPath = Path(f"{str(self.rootPath)}_SR") 

        fireName = self.cfg.fireEvent.name
        print("------------------------- Download Start ... ----------------------------------")
        downLoadList = (imgCol).aggregate_array('IMG_LABEL').getInfo()
        self.printList(downLoadList, 'downloadList: ')
        print("-------------------------------------------------------------------------------")

        # self.zipPath = self.rootPath / "{:}_{:}m_{:}_GEE_download_zip".format(fireName, scale, pathKeyWord)
        # self.tifPath = self.rootPath / "{:}_{:}m_{:}_Tif_collection".format(fireName, scale, pathKeyWord)
        # self.pngPath = self.rootPath / "{:}_{:}m_{:}_PNG_collection".format(fireName, scale, pathKeyWord)
        # self.rgbPath = self.rootPath / "{:}_{:}m_{:}_RGB_collection".format(fireName, scale, pathKeyWord)

        self.zipPath = self.rootPath / "{:}_zip".format(pathKeyWord)
        self.tifPath = self.rootPath / "{:}_Tif".format(pathKeyWord)
        self.pngPath = self.rootPath / "{:}_PNG".format(pathKeyWord)
        self.rgbPath = self.rootPath / "{:}_RGB".format(pathKeyWord)

        num = imgCol.size().getInfo()
        imgColList = imgCol.toList(num)
        for i in range(0, num):
            img = ee.Image(imgColList.get(i))
            saveName = "{}".format(img.get('IMG_LABEL').getInfo())

            if len(bands4download) > 0:
                url = (img.select(bands4download)
                    .getDownloadURL({
                        'region': self.roi,  # roi.toGeoJSON()['coordinates'],  # roi.serialize(),
                        'scale': scale,
                        'crs': self.cfg.fireEvent.crs,
                        'filePerBand': True,
                        'formatOptions': { # Cloud-Optimized TIF
                                "cloudOptimized": True
                        }
                }))
            else:
                url = (img
                    .getDownloadURL({
                        'region': self.roi,  # roi.toGeoJSON()['coordinates'],  # roi.serialize(),
                        'scale': scale,
                        'crs': self.cfg.fireEvent.crs,
                        'filePerBand': True,
                        'formatOptions': { # Cloud-Optimized TIF
                                "cloudOptimized": True
                    }
                }))

            if not os.path.exists(self.zipPath):
                os.makedirs(self.zipPath)

            print("{}:\n {}".format(saveName, url))
            self.url_download(url=url, saveName=f"{saveName}.zip")

            unzipPath = self.zipPath / "unzipedFiles"
            self.un_zip(saveName, unzipPath)

            renamePath = self.zipPath / "renamedFiles"
            renamedName = saveName

            os.system("rd/s/q {}".format(renamePath))

            if not os.path.exists(renamePath):
                os.makedirs(renamePath)
            self.batchReName(unzipPath, renamePath, renamedName)

            from utils.gdal_tif2rgb import tifBand2png_GDAL, bandsMerge2tif
            bandsMerge2tif(renamePath, saveName, self.tifPath, saveName, stretchFlag=False)

            tifBand2png_GDAL(renamePath, self.pngPath, pngSretch=95.0)

            # ## ============== delete directory =====================
            # os.system("rd/s/q " + str(unzipPath))
            
            if toRGBflag:
                self.pngBand2rgb(saveName, bands=rgbVisBands)

        ''' Remove Zip Files '''
        os.system("rd/s/q " + str(self.zipPath))

    def url_download(self, url, saveName):
        logging.basicConfig(
            format='%(asctime)s %(levelname)s %(message)s',
            level=logging.INFO,
            stream=sys.stdout)
        
        # file_path = os.path.join(os.getcwd(),'dir_name/file_name')
        filePath = self.zipPath / saveName

        if os.path.isfile(filePath):
            os.system("rm {}".format(filePath))
            logging.info("Existed file deleted: {}".format(saveName))
        else:
            logging.info("File doesn't exist.")
        # replace with url you need

        # if dir 'dir_name/' doesn't exist
        if not os.path.exists(self.zipPath):
            logging.info("Make direction: {}".format(self.zipPath))
            os.mkdir(self.zipPath)

        def down(_save_path, _url):
            try:
                Request.urlretrieve(_url, _save_path)
                return True
            except:
                print('\nError when retrieving the URL:\n{}'.format(_url))
                return False

        # logging.info("Downloading file.")
        down(filePath, url)
        print("------- Download Finished! ---------")

    def un_zip(self, dataName, unzipPath):
        """ unzip zip file """
        zip_file = zipfile.ZipFile(self.zipPath / "{}.zip".format(dataName))
        if os.path.isdir(unzipPath):
            pass
        else:
            os.mkdir(unzipPath)
        for names in zip_file.namelist():
            zip_file.extract(names, unzipPath)
        zip_file.close()

    
    def batchReName(self, dataPath, savePath, saveName):
        print("dataPath: " + str(dataPath))
        for file in os.listdir(dataPath):
            format = "." + file.split(".")[-1]
            orginalName = file.split(".")[0]
            saveFileName = file.replace(orginalName, saveName)

            if format == ".tif":  # and ('angle' not in file)
                if os.path.isfile(savePath / saveFileName):
                    os.system("rm {}".format(str(savePath / saveFileName)))
                os.rename(dataPath / file, savePath / saveFileName)

    def pngBand2rgb(self, dataName, bands):
        R = imread(self.pngPath / "{}.{}.png".format(dataName, bands[0]))  # read data
        G = imread(self.pngPath / "{}.{}.png".format(dataName, bands[1]))
        B = imread(self.pngPath / "{}.{}.png".format(dataName, bands[2]))

        jpg_data = np.zeros([R.shape[0], R.shape[1], 3])
        jpg_data[..., 0] = R
        jpg_data[..., 1] = G
        jpg_data[..., 2] = B

        # jpg_data = data.transpose(1, 2, 0)
        if not os.path.exists(self.rgbPath):
            os.makedirs(self.rgbPath)
        imsave(self.rgbPath / "{}.png".format(dataName), jpg_data.astype(np.uint8))


    def ee_image_2_array(self, img, aoi, bandList):
        """ this function has limit on the data size """
        # Get 2-d pixel array for AOI - returns feature with 2-D pixel array as property per band.
        band_arrs = img.sampleRectangle(region=aoi)

        # Get individual band arrays.
        np_arr_list = []
        for idx, band in enumerate(bandList):
            band_arr = band_arrs.get(bandList[idx])
            np_arr = np.array(band_arr.getInfo())
            np_arr_list.append(np_arr)

        return np.dstack(tuple(np_arr_list))