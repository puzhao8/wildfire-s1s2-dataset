import ee
from eo_class.eo_dataset import EO_DATASET
# from ee_data_export_funs import printList

import logging
logger = logging.getLogger(__name__)

class SAR(EO_DATASET):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.cfg = cfg
        self.driveFolder = f"{self.driveFolder}/SAR"

        self.logRt_Flag = cfg.sar_logRt_Flag

        self.sarMasterMode = cfg.sarMasterMode
        self.numOfMonths = cfg.numOfMonths
        self.waterMaskFlag = False #cfg.waterMaskFlag

        self.sarMeanDict = {}
        self.sarStdDict = {}
        self.liaImgCol = ee.ImageCollection([])
        self.sarImgCol = ee.ImageCollection([])

    def sarRescaleToOne(self, img):
        return (ee.Image(img.select(['VV', 'VH', 'CR'])
                            .clamp(-25.0, 5).unitScale(-25.0, 5).float())
                            .addBands(img.select('RFDI').clamp(0, 10).unitScale(0, 10).float())
                            .copyProperties(img, img.propertyNames())
            )

    def imgConv(self, img):
        G_kernel = ee.Kernel.gaussian(11)
        return img.convolve(G_kernel)\
                    .reproject(crs=img.projection().crs(), scale=20)\
                    .copyProperties(img, img.propertyNames())


    # def sar_quary_and_preprocess(self):
    # def __call__(self):

    def query_wo_processing(self):
        logger.info("\n----------------- Sentinel-1 ------------------------")
        S1_filtered = ee.ImageCollection(ee.ImageCollection("COPERNICUS/S1_GRD")
                        .filterBounds(self.roi)
                        .filterMetadata('instrumentMode', "equals", 'IW')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                    ).select(['VH', 'VV'])

        S1_filtered = S1_filtered.filterDate(self.checkStartDate, self.checkEndDate)

        if 'orbNumList' in self.cfg.fireEvent.keys():
            orbNumList = self.cfg.fireEvent['orbNumList']
            S1_filtered = S1_filtered.filter(ee.Filter.inList(opt_leftField='relativeOrbitNumber_start', opt_rightValue=orbNumList))
        
        self.sarImgCol = self.group_S1_by_date_orbit(S1_filtered)\
                                .map(self.add_CR)\
                                .map(self.sarRescaleToOne)



    def query_and_processing(self):   
        print("\n----------------- Sentinel-1 ------------------------")
        S1_filtered = ee.ImageCollection(ee.ImageCollection("COPERNICUS/S1_GRD")
                        .filterBounds(self.roi)
                        .filterMetadata('instrumentMode', "equals", 'IW')
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                    )

        # self.cfg.fireEvent.crs = S1_filtered.first().select(0).projection().crs().getInfo()
        # print(f"CRS -> {self.cfg.fireEvent.crs}")

        if 'orbNumList' in self.cfg.fireEvent.keys():
            orbNumList = self.cfg.fireEvent['orbNumList']
            S1_filtered = S1_filtered.filter(ee.Filter.inList(opt_leftField='relativeOrbitNumber_start', opt_rightValue=orbNumList))
        
        sarImgCol = S1_filtered.filterDate(self.checkStartDate, self.checkEndDate)

        ''' Lee Filtering '''
        if False: 
            sarImgCol = sarImgCol.map(refinedLeeFlt)
                    
        self.sarImgCol_grouped = (self.group_S1_by_date_orbit(sarImgCol)
                                .map(self.add_CR)
                                .map(self.sarRescaleToOne)
                                .map(self.imgConv)
                                # .map(self.normalize_bySpatialMeanStd) # added Feb. 25, 2021
                                .select(['CR', 'RFDI', 'VH', 'VV'])
                            )

        print("SAR dateRange: [" + self.checkStartDate.format().slice(0, 10).getInfo() + ", "
                + self.checkEndDate.format().slice(0, 10).getInfo() + "]")

        print('sarImgCol_grouped: ')
        # self.printList(self.sarImgCol_grouped.aggregate_array('IMG_LABEL').getInfo())

        # """#= == == == == == == == == == == == == == == == == == OrbitList == == == == == == == == == == == == == == == == == == == == == ="""
        # ------- Method - 2: aggregate_array for obtaining distinct orbitKey -------------------------------------
        self.orbitKeyList = ee.List(self.sarImgCol_grouped.aggregate_array("Orbit_Key")).distinct().sort()
        print("orbitKeyList: ", self.orbitKeyList.getInfo())

        """ if there is no need to do logRt, stop here """
        if not self.logRt_Flag: 
            self.sarImgCol = self.sarImgCol_grouped
            return 
        
        """ Two months before wildfire Happened """
        historyImgCol = (self.sarImgCol_grouped.filterDate(ee.Date(self.fireStartDate).advance((-1)*self.numOfMonths, 'month'), self.fireStartDate))
        
        """ Last Year, Same Period """
        # historyImgCol = (S1_filtered.filterDate(ee.Date(self.fireStartDate).advance(-1, 'year'), 
        #                         ee.Date(self.fireStartDate).advance(2, 'month').advance(-1, 'year')))

        ''' Lee Filtering '''
        if False: 
            historyImgCol = historyImgCol.map(refinedLeeFlt)

        # historyImgCol = (historyImgCol.map(self.set_group_index_4_S1)
        #                                 .map(self.add_CR)
        #                                 .map(self.sarRescaleToOne)
        #                                 .map(self.normalize_bySpatialMeanStd) # added Feb. 25, 2021
        #                             )

            # printList(historyImgCol.aggregate_array('IMG_LABEL').getInfo(), historyImgCol)
        "=============================>   compute kmap for all SAR orbits  <=========================="   
        # if 'sarExportDates' in self.cfg.fireEvent.keys():
        #     self.sarImgCol_grouped = sarImgCol_grouped.filter(ee.Filter.inList(opt_leftField='GROUP_INDEX', opt_rightValue=sarExportDates))

        for orbKey in self.orbitKeyList.getInfo():
            self.orbKey = orbKey
            # orbKey = 'DSC42'
            print("==> orbKey checking: ", self.orbKey)
            orbImgCol = ee.ImageCollection(self.sarImgCol_grouped.filter(ee.Filter.equals('Orbit_Key', orbKey)))

            if False: # LIA computation
                liaImg = self.compute_LIA(orbImgCol.first())
                self.liaImgCol = self.liaImgCol.merge(ee.ImageCollection.fromImages([liaImg]))

            print("-----------------------------------------------------\n\n")
            print('===> orbImgCol: {} <==='.format(orbKey))
            self.printList(orbImgCol.aggregate_array('IMG_LABEL').getInfo(), orbKey)

            num = orbImgCol.size().getInfo()
            orbImgList = orbImgCol.toList(num)

            if 'master' == self.sarMasterMode:
                orbMasterDate = ee.Date(self.cfg.fireEvent[orbKey])
                print(f"orbMasterDate {orbKey}: {self.cfg.fireEvent[orbKey]}")
                self.sarMeanDict[orbKey] = ee.Image(
                    self.sarImgCol_grouped.filterDate(orbMasterDate, orbMasterDate.advance(1, 'day')).first())

                logRtImgCol = (orbImgCol
                        .map(self.add_logRt_master)
                        # .map(self.imgConv) # added on 2020/08/23
                    )
                self.sarImgCol = self.sarImgCol.merge(logRtImgCol).sort("IMG_LABEL", True)


            """ Compute mean and stdDev with the stdDev of historical time series for one given orbit """
            orbHistoryImgCol = historyImgCol.filter(ee.Filter.equals('Orbit_Key', orbKey))

            if ('master' != self.sarMasterMode) and (orbHistoryImgCol.size().getInfo() > 2): # added on Dec-11-2020
                # self.printList(orbHistoryImgCol.aggregate_array('IMG_LABEL').getInfo(), f"{orbKey} prefire images")

                if 'median' == self.sarMasterMode:
                    self.compute_median_stdDev(orbHistoryImgCol)

                elif 'mean' == self.sarMasterMode:
                    self.compute_mean_stdDev(orbHistoryImgCol)
                
                logRtImgCol = (orbImgCol
                        .map(self.add_logRt)
                        .map(self.add_kmap)
                        # .map(self.add_rmap)
                        # .map(self.imgConv) # added on 2020/08/23
                    )
                self.sarImgCol = self.sarImgCol.merge(logRtImgCol).sort("IMG_LABEL", True)

    def normalize_bySpatialMeanStd(self, img):
        spatial_mean = img.reduceRegion(
                                reducer=ee.Reducer.mean(), 
                                geometry=self.cfg.fireEvent.roi, 
                                scale = 20,
                                maxPixels = 1e10,
                                # tileScale = 4
                            ).toImage()

        # spatial_stdDev = img.reduceRegion(
        #                         reducer=ee.Reducer.stdDev(), 
        #                         geometry=self.cfg.fireEvent.roi, 
        #                         scale = 100,
        #                         maxPixels = 1e10,
        #                         # tileScale = 4
        #                     ).toImage()

        # .divide(spatial_stdDev)
        return img.subtract(spatial_mean).copyProperties(img, img.propertyNames())
    
    def compute_mean_stdDev(self, orbHistoryImgCol):
        # orbMeanImg = ee.Image(orbHistoryImgCol.reduce(ee.Reducer.mean())
        #                 .select(['VV_mean', 'VH_mean', 'CR_mean', 'RFDI_mean']))
        
        orbMeanImg = ee.Image(orbHistoryImgCol.mean()
                        .select(['CR', 'RFDI', 'VH', 'VV'])
                        .rename(['CR_mean', 'RFDI_mean', 'VH_mean', 'VV_mean']))

        self.sarMeanDict[self.orbKey] = ee.Image(orbMeanImg.setMulti({'IMG_LABEL': 'SAR_MEAN_{}'.format(self.orbKey)}))

        orbHisImgColSize = orbHistoryImgCol.size()
        orbStdImg = ee.Image(orbHistoryImgCol.reduce(ee.Reducer.stdDev()).add(0.001)
                        .select(['CR_stdDev', 'RFDI_stdDev', 'VH_stdDev', 'VV_stdDev'])
                        .rename(['CR_std', 'RFDI_std', 'VH_std', 'VV_std']))
                        # .multiply(orbHisImgColSize).divide(orbHisImgColSize.subtract(1)).sqrt())
        self.sarStdDict[self.orbKey] = ee.Image(orbStdImg.setMulti({'IMG_LABEL': 'SAR_STD_{}'.format(self.orbKey)}))

    def compute_median_stdDev(self, orbHistoryImgCol):
        orbMeanImg = ee.Image(orbHistoryImgCol.reduce(ee.Reducer.median())
                        .select(['CR_median', 'RFDI_median', 'VH_median', 'VV_median'])
                        .rename(['CR_mean', 'RFDI_mean', 'VH_mean', 'VV_mean']))
        self.sarMeanDict[self.orbKey] = ee.Image(orbMeanImg.setMulti({'IMG_LABEL': 'SAR_MEDIAN_{}'.format(self.orbKey)}))

        
        orbHisImgColSize = orbHistoryImgCol.size()
        orbStdImg = ee.Image(orbHistoryImgCol.map(self.add_d2Map)
                        .reduce(ee.Reducer.median()).multiply(1.4826).add(0.001)
                        .select(['d2CR_median', 'd2RFDI_median', 'd2VH_median', 'd2VV_median'])
                        .rename(['CR_std', 'RFDI_std', 'VH_std', 'VV_std']))
                        # .multiply(orbHisImgColSize).divide(orbHisImgColSize.subtract(1)).sqrt())
        self.sarStdDict[self.orbKey] = ee.Image(orbStdImg.setMulti({'IMG_LABEL': 'SAR_mSTD_{}'.format(self.orbKey)}))

    def add_logRt_master(self, slaveImg):
        meanImg = self.sarMeanDict[self.orbKey]
        logRt = (meanImg.select(['CR', 'RFDI', 'VH', 'VV'])
                .subtract(slaveImg.select(['CR', 'RFDI', 'VH', 'VV']))
                .select(['CR', 'RFDI', 'VH', 'VV'])
                .rename(['dCR', 'dRFDI', 'dVH', 'dVV'])
            )
        if self.waterMaskFlag:
            logRt = self.mask_water(logRt)
        
        return slaveImg.addBands(logRt)

    """ logRt = temporal_mean - slaveImg (postfire observation) """
    def add_logRt(self, slaveImg):
        meanImg = self.sarMeanDict[self.orbKey]
        stdDevImg = self.sarStdDict[self.orbKey]
        logRt = (meanImg.select(['CR_mean', 'RFDI_mean', 'VH_mean', 'VV_mean'])
                        .rename(['CR', 'RFDI', 'VH', 'VV'])
                .subtract(slaveImg.select(['CR', 'RFDI', 'VH', 'VV'])).multiply(-1)
                .select(['CR', 'RFDI', 'VH', 'VV'])
                .rename(['dCR', 'dRFDI', 'dVH', 'dVV'])
            )
        if self.waterMaskFlag:
            logRt = self.mask_water(logRt)
        
        return (slaveImg.addBands(logRt)
                .addBands(meanImg)
                .addBands(stdDevImg))

    def kMap_clip(self, img): return (img.select(['kCR', 'kRFDI', 'kVH', 'kVV']).clamp(-3,3)
                                    .add(3).divide(6).multiply(255).toUint8()
                                    .toFloat().divide(255).multiply(6).subtract(3)
                                    .setMulti({"IMG_LABEL": img.get("IMG_LABEL")})
                                )
    
    """ k = (x - temporal_Mean) / temporal_StdDev """
    def add_kmap(self, logRtImg): 
        stdDevImg = self.sarStdDict[self.orbKey].select(['CR_std', 'RFDI_std', 'VH_std', 'VV_std']).rename(['CR', 'RFDI', 'VH', 'VV'])
        kmap = ee.Image(logRtImg.select(['dCR', 'dRFDI', 'dVH', 'dVV'])
                                .rename(['CR', 'RFDI', 'VH', 'VV'])
                    .divide(stdDevImg) # for k(x)
                    .select(['CR', 'RFDI', 'VH', 'VV'])
                    .rename(['kCR', 'kRFDI', 'kVH', 'kVV'])
                )
        kMap = self.kMap_clip(kmap)
        return logRtImg.addBands(kMap)

    """ r = (x - temporal_Mean) / temporal_Mean """
    def add_rmap(self, logRtImg):
        meanImg = self.sarMeanDict[self.orbKey].select(['CR_mean', 'RFDI_mean', 'VH_mean', 'VV_mean']).rename(['CR', 'RFDI', 'VH', 'VV'])
        kmap = ee.Image(logRtImg.select(['dCR', 'dRFDI', 'dVH', 'dVV'])
                                .rename(['CR', 'RFDI', 'VH', 'VV'])
                    .divide(meanImg.abs().sqrt()) # for r(x)
                    .rename(['rCR', 'rRFDI', 'rVH', 'rVV'])
                )
        return logRtImg.addBands(kmap)


    ''' Median Absolute Deviation (MAD) '''
    def add_d2Map(self, img): 
        dMap = (self.sarMeanDict[self.orbKey].select(['CR_mean', 'RFDI_mean', 'VH_mean', 'VV_mean'])
                            .rename(['CR', 'RFDI', 'VH', 'VV'])
                            .subtract(img.select(['CR', 'RFDI', 'VH', 'VV']))
                            .abs()
                            .select(['CR', 'RFDI', 'VH', 'VV'])
                            .rename(['d2CR', 'd2RFDI', 'd2VH', 'd2VV']))
        return img.addBands(dMap).select(['d2CR', 'd2RFDI', 'd2VH', 'd2VV'])

    """ SAR Group Days """
    def set_group_index_4_S1(self, img):
        orbitKey = (ee.String(img.get("orbitProperties_pass")).replace('DESCENDING', 'DSC').replace('ASCENDING', 'ASC')
                    .cat(ee.Number(img.get("relativeOrbitNumber_start")).int().format()))
        Date = (img.date().format().slice(0, self.cfg.labelShowLevel)
                    .replace('-', '').replace('-', '').replace(':', '').replace(':', ''))
        Name = (Date).cat('_').cat(orbitKey)

        groupIndex = img.date().format().slice(0, self.cfg.groupLevel)  # 2017 - 07 - 23T14:11:22(len: 19)
        return img.setMulti({
            'GROUP_INDEX': groupIndex,
            'IMG_LABEL': Name,
            'Orbit_Key': orbitKey
        })

    # "group by" date
    def group_S1_by_date_orbit(self, imgcollection):
        imgCol_sort = imgcollection.sort("system:time_start")
        imgCol = imgCol_sort.map(self.set_group_index_4_S1)
        d = imgCol.distinct(['GROUP_INDEX'])
        di = ee.ImageCollection(d)
        # date_eq_filter = (ee.Filter.equals(leftField='system:time_end',
        #                                    rightField='system:time_end'))

        date_eq_filter = (ee.Filter.And(
            # ee.Filter.equals(leftField='GROUP_INDEX', rightField='GROUP_INDEX')
            # , ee.Filter.equals(leftField='Orbit_Key', rightField='Orbit_Key')
            ee.Filter.equals(leftField='IMG_LABEL', rightField='IMG_LABEL')
            , ee.Filter.equals(leftField='transmitterReceiverPolarisation', rightField='transmitterReceiverPolarisation')
        ))

        saveall = ee.Join.saveAll("to_mosaic")
        j = saveall.apply(di, imgCol, date_eq_filter)
        ji = ee.ImageCollection(j)

        def mosaicImageBydate(img):
            ## Old version
            # mosaiced = ee.ImageCollection.fromImages(img.get('to_mosaic')).mosaic().updateMask(1)
            # return ee.Image(mosaiced).copyProperties(img, img.propertyNames())

            imgCol2mosaic = ee.ImageCollection.fromImages(img.get('to_mosaic'))
            firstImgGeom = imgCol2mosaic.first().geometry()
            mosaicGeom = ee.Geometry(imgCol2mosaic.iterate(self.unionGeomFun, firstImgGeom))
            mosaiced = imgCol2mosaic.mosaic().copyProperties(img, img.propertyNames())
            return ee.Image(mosaiced).set("system:footprint", mosaicGeom)  # lost

        imgcollection_grouped = ji.map(mosaicImageBydate)
        return ee.ImageCollection(imgcollection_grouped.copyProperties(imgCol, imgCol.propertyNames()))


    def toNatural(self, img):
        return ee.Image(10.0).pow(img.divide(10.0))

    def toDB(self, img):
        return ee.Image(img).log10().multiply(10.0)

    def add_CR(self, img):
        img_nat = self.toNatural(img.select(['VH', 'VV']))

        # RFDI = (b("VV")-b("VH"))/(b("VV")+b("VH")) because VV > VH
        RFDI = self.toDB(img_nat.normalizedDifference(['VV', 'VH']).select('nd').rename('RFDI')).multiply(-1)
        CR = img.expression('b("VH")-b("VV")').rename("CR")  
        # CR = toDB(img_nat.expression('4 * b("VH") / (b("VV") + b("VH"))').abs()).rename('CR');
        return ee.Image(img.addBands(RFDI).addBands(CR).copyProperties(img, img.propertyNames()))

    """ Local Incidence Angle """
    def compute_LIA(self, image):
        import math
        degAdjustList = ee.List([180.0, 180.0])
        if(ee.String(image.get('orbitProperties_pass')).getInfo() == 'ASCEDNING'):
            degAdjustList = ee.List([270.0, 360.0])
        
        # Get the coords as a transposed array
        coords = ee.Array(image.geometry().coordinates().get(0)).transpose()
        crdLons = ee.List(coords.toList().get(0))
        crdLats = ee.List(coords.toList().get(1))
        minLon = crdLons.sort().get(0)
        maxLon = crdLons.sort().get(-1)
        minLat = crdLats.sort().get(0)
        maxLat = crdLats.sort().get(-1)

        azimuth = (ee.Number(crdLons.get(crdLats.indexOf(minLat))).subtract(minLon)
                        .atan2(ee.Number(crdLats.get(crdLons.indexOf(minLon))).subtract(minLat))
                        .multiply(180.0/math.pi)
                        .add(degAdjustList.get(0))) # 270 for ASC, 180 for DSC
        azimuthEdge =  (ee.Feature(ee.Geometry.LineString([crdLons.get(crdLats.indexOf(minLat)), minLat,
                minLon, crdLats.get(crdLons.indexOf(minLon))]), { 'azimuth': azimuth}).copyProperties(image))
        
        trueAzimuth = azimuthEdge.get('azimuth')
        rotationFromNorth = ee.Number(trueAzimuth).subtract(degAdjustList.get(1))

        # Correct the across-range-look direction
        s1_inc = image.select('angle')
        s1_azimuth = (ee.Terrain.aspect(s1_inc)
                        .reduceRegion(reducer=ee.Reducer.mean(), geometry=s1_inc.get('system:footprint'), scale=100, maxPixels=154617270)
                        .get('aspect'))
        s1_azimuth = ee.Number(s1_azimuth).add(rotationFromNorth)

        #  Here we derive the terrain slope and aspect
        srtm =  ee.Image("USGS/SRTMGL1_003")
        srtm_slope = ee.Terrain.slope(srtm).select('slope')
        srtm_aspect = ee.Terrain.aspect(srtm).select('aspect')

        # And then the projection of the slope
        slope_projected = srtm_slope.multiply(ee.Image.constant(s1_azimuth).subtract(srtm_aspect).multiply(math.pi/180).cos())
        lia = s1_inc.subtract(ee.Image.constant(90).subtract(ee.Image.constant(90).subtract(slope_projected))).abs()
        
        # And finally the local incidence angle
        # slope_projected2 = srtm_slope.multiply(ee.Image.constant(trueAzimuth).subtract(90.0).subtract(srtm_aspect).multiply(math.pi/180).cos())
        # lia2 = s1_inc.subtract(ee.Image.constant(90).subtract(ee.Image.constant(90).subtract(slope_projected2))).abs()
        return lia.rename('angle').setMulti({'IMG_LABEL': ee.String('LIA_').cat(ee.String(image.get('IMG_LABEL')).split('_').get(1))})


    # Functions to convert from/to dB
    def toNatural_singleBand(self, img):
        return ee.Image(10.0).pow(img.select(0).divide(10.0))

    def refined_lee(self, img):
        
        # Refined Lee Speckle Filter
        # Guido Lemoine: https:code.earthengine.google.com/b9542a4e3ca64a57415ce7a3a5b1a80f
        
        # img must be in natural units, i.e. not in dB!
        # Set up 3x3 kernels 
        weights3 = ee.List.repeat(ee.List.repeat(1,3),3)
        kernel3 = ee.Kernel.fixed(3,3, weights3, 1, 1, False)

        mean3 = img.reduceNeighborhood(ee.Reducer.mean(), kernel3)
        variance3 = img.reduceNeighborhood(ee.Reducer.variance(), kernel3)

        # Use a sample of the 3x3 windows inside a 7x7 windows to determine gradients and directions
        sample_weights = ee.List([[0,0,0,0,0,0,0], [0,1,0,1,0,1,0],[0,0,0,0,0,0,0], [0,1,0,1,0,1,0], [0,0,0,0,0,0,0], [0,1,0,1,0,1,0],[0,0,0,0,0,0,0]])

        sample_kernel = ee.Kernel.fixed(7,7, sample_weights, 3,3, False)

        # Calculate mean and variance for the sampled windows and store as 9 bands
        sample_mean = mean3.neighborhoodToBands(sample_kernel) 
        sample_var = variance3.neighborhoodToBands(sample_kernel)

        # Determine the 4 gradients for the sampled windows
        gradients = sample_mean.select(1).subtract(sample_mean.select(7)).abs()
        gradients = gradients.addBands(sample_mean.select(6).subtract(sample_mean.select(2)).abs())
        gradients = gradients.addBands(sample_mean.select(3).subtract(sample_mean.select(5)).abs())
        gradients = gradients.addBands(sample_mean.select(0).subtract(sample_mean.select(8)).abs())

        # And find the maximum gradient amongst gradient bands
        max_gradient = gradients.reduce(ee.Reducer.max())

        # Create a mask for band pixels that are the maximum gradient
        gradmask = gradients.eq(max_gradient)

        # duplicate gradmask bands: each gradient represents 2 directions
        gradmask = gradmask.addBands(gradmask)

        # Determine the 8 directions
        directions = sample_mean.select(1).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(7))).multiply(1)
        directions = directions.addBands(sample_mean.select(6).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(2))).multiply(2))
        directions = directions.addBands(sample_mean.select(3).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(5))).multiply(3))
        directions = directions.addBands(sample_mean.select(0).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(8))).multiply(4))

        # # The next 4 are the not() of the previous 4
        directions = directions.addBands(directions.select(0).eq(0).multiply(5))
        directions = directions.addBands(directions.select(1).eq(0).multiply(6))
        directions = directions.addBands(directions.select(2).eq(0).multiply(7))
        directions = directions.addBands(directions.select(3).eq(0).multiply(8))
        
        # Mask all values that are not 1-8
        directions = directions.updateMask(gradmask)

        # "collapse" the stack into a singe band image (due to masking, each pixel has just one value (1-8) in it's directional band, and is otherwise masked)
        directions = directions.reduce(ee.Reducer.sum())  

        #pal = ['ffffff','ff0000','ffff00', '00ff00', '00ffff', '0000ff', 'ff00ff', '000000']
        #Map.addLayer(directions.reduce(ee.Reducer.sum()), {min:1, max:8, palette: pal}, 'Directions', False)

        sample_stats = sample_var.divide(sample_mean.multiply(sample_mean))

        # Calculate localNoiseVariance
        sigmaV = sample_stats.toArray().arraySort().arraySlice(0,0,5).arrayReduce(ee.Reducer.mean(), [0])

        # Set up the 7*7 kernels for directional statistics
        rect_weights = ee.List.repeat(ee.List.repeat(0,7),3).cat(ee.List.repeat(ee.List.repeat(1,7),4))

        diag_weights = ee.List([[1,0,0,0,0,0,0], [1,1,0,0,0,0,0], [1,1,1,0,0,0,0], [1,1,1,1,0,0,0], [1,1,1,1,1,0,0], [1,1,1,1,1,1,0], [1,1,1,1,1,1,1]])

        rect_kernel = ee.Kernel.fixed(7,7, rect_weights, 3, 3, False)
        diag_kernel = ee.Kernel.fixed(7,7, diag_weights, 3, 3, False)

        # Create stacks for mean and variance using the original kernels. Mask with relevant direction.
        dir_mean = img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel).updateMask(directions.eq(1))
        dir_var = img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel).updateMask(directions.eq(1))

        dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel).updateMask(directions.eq(2)))
        dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel).updateMask(directions.eq(2)))

        # and add the bands for rotated kernels
        for i in range(1, 4):
            dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel.rotate(i)).updateMask(directions.eq(2*i+1)))
            dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel.rotate(i)).updateMask(directions.eq(2*i+1)))
            dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel.rotate(i)).updateMask(directions.eq(2*i+2)))
            dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel.rotate(i)).updateMask(directions.eq(2*i+2)))

        # "collapse" the stack into a single band image (due to masking, each pixel has just one value in it's directional band, and is otherwise masked)
        dir_mean = dir_mean.reduce(ee.Reducer.sum())
        dir_var = dir_var.reduce(ee.Reducer.sum())

        # A finally generate the filtered value
        varX = dir_var.subtract(dir_mean.multiply(dir_mean).multiply(sigmaV)).divide(sigmaV.add(1.0))

        b = varX.divide(dir_var)

        result = dir_mean.add(b.multiply(img.subtract(dir_mean)))
        return(result.arrayFlatten([['sum']]))


    def refinedLeeFlt(self, img):
        VH_Lee = self.toDB(refined_lee(toNatural_singleBand(img.select('VH')))).select('sum').rename('VH')
        VV_Lee = self.toDB(refined_lee(toNatural_singleBand(img.select('VV')))).select('sum').rename('VV')
        img = img.addBands(VH_Lee, ['VH'], True).addBands(VV_Lee, ['VV'], True)
        return img