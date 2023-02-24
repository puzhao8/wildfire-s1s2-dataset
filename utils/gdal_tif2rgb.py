from pathlib import Path, PureWindowsPath
# from osgeo import gdal
import gdal
import os, glob
# import filetype as ftype
import numpy as np
# import matplotlib.pyplot as plt
# from scipy.ndimage import gaussian_filter
from imageio import imsave, imread
from astropy.visualization import PercentileInterval
import tifffile as tiff

interval_100 = PercentileInterval(100.0)
interval_98 = PercentileInterval(98.0)
interval_95 = PercentileInterval(95.0)


class GRID:
    # read image files
    def read_data(self, url):
        
        if not isinstance(url, str): url = str(url)
        raster = gdal.Open(url)  # open file

        im_width = raster.RasterXSize  # get width
        im_height = raster.RasterYSize  # get height

        im_geotrans = raster.GetGeoTransform()  # get geoTransform
        im_proj = raster.GetProjection()  # get Projection
        im_data = raster.ReadAsArray(0, 0, im_width, im_height)  # read data as array

        del raster
        return im_proj, im_geotrans, im_data

    # write tiff file
    def write_data(self, url, im_proj, im_geotrans, im_data, bandNameList):
        # gdal data types include:
        # gdal.GDT_Byte,
        # gdal .GDT_UInt16, gdal.GDT_Int16, gdal.GDT_UInt32, gdal.GDT_Int32,
        # gdal.GDT_Float32, gdal.GDT_Float64

        # check the datatype of raster data
        if 'int8' in im_data.dtype.name:
            datatype = gdal.GDT_Byte
        elif 'int16' in im_data.dtype.name:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32

        # get the dimension
        if len(im_data.shape) == 3:
            im_bands, im_height, im_width = im_data.shape
        else:
            im_bands, (im_height, im_width) = 1, im_data.shape

        # create output folder
        outputFolder = os.path.split(url)[0]
        if not os.path.exists(outputFolder): os.makedirs(outputFolder)

        # create the output file
        driver = gdal.GetDriverByName("GTiff")  # specify the format
        if not isinstance(url, str): url = str(url)
        raster = driver.Create(url, im_width, im_height, im_bands, datatype, options=["TILED=YES",
                                                                                    "COMPRESS=LZW",
                                                                                    "INTERLEAVE=BAND"])

        if (raster != None):
            raster.SetGeoTransform(im_geotrans)  # write affine transformation parameter
            raster.SetProjection(im_proj)  # write Projection
        else:
            print("Fails to create output file !!!")

        if im_bands == 1:
            rasterBand = raster.GetRasterBand(1)
            rasterBand.SetNoDataValue(0)

            rasterBand.SetDescription(bandNameList[0])
            rasterBand.WriteArray(im_data)

        else:
            # print("im_bands", im_bands)
            for bandIdx, bandName in zip(range(0, im_bands), bandNameList):
                # print(bandIdx)
                # print(bandName)
                bandNum = bandIdx + 1
                rasterBand = raster.GetRasterBand(bandNum)
                rasterBand.SetNoDataValue(0)

                rasterBand.SetDescription(bandName)
                rasterBand.WriteArray(im_data[bandIdx, ...])

        del raster


def read_tif_and_get_bands(dataPath, dataName, requiredBands):
    if '.tif' in dataName:
        dataName = dataName[:-4]
    raster = gdal.Open(str(Path(dataPath) / "{}.tif".format(dataName)))  # open file

    data = raster.ReadAsArray(0, 0)  # read data as array
    mask = raster.GetRasterBand(1).GetMaskBand().ReadAsArray(0, 0)
    # print("data shape: {}, mask shape: {}".format(data.shape, mask.shape))

    bandNameList = []
    numBands = raster.RasterCount

    if len(data.shape) == 2:
        data = data[np.newaxis, ...]

    DATA = np.zeros([len(requiredBands), data.shape[1], data.shape[2]])

    cnt = 0
    for i in range(numBands):
        rasterBand = raster.GetRasterBand(i + 1)
        bandName = rasterBand.GetDescription()

        print("bandName: {}".format(bandName))
        bandNameList.append(bandName)
        if bandName in requiredBands:
            DATA[cnt, ...] = data[i, ...]
            cnt = cnt + 1

    # print(bandNameList)
    # print("cnt: {}".format(cnt))
    if cnt != len(requiredBands):
        print("----------------------------------------------------")
        print("There is no required bands: {}".format(requiredBands))
        DATA, mask = None, None

    return DATA, mask[np.newaxis, ...] / 255


def tif2rgb(dataPath, dataName, savePath, saveName):
    run = GRID()

    proj, geotrans, data = run.read_data(
        dataPath + dataName + ".tif")  # read data

    print("data shape {}".format(data.shape))

    if len(data.shape) == 3:
        data = data[0:3, :, :]
        jpg_data = data.transpose(1, 2, 0)

    if len(data.shape) == 2:
        # jpg_data = np.zeros([data.shape[0], data.shape[1], 3])
        # jpg_data[..., 0] = data
        # jpg_data[..., 1] = data
        # jpg_data[..., 2] = data
        # jpg_data = np.uint8(jpg_data *255)
        jpg_data = data

    if not os.path.exists(savePath):
        os.makedirs(savePath)
    print("{}".format(saveName))
    plt.imsave(savePath + saveName + ".png", jpg_data, cmap=plt.cm.Greens)


def tifBand2png_GDAL(dataPath, savePath, pngSretch):
    if not os.path.exists(savePath):
        os.makedirs(savePath)

    fileList = os.listdir(dataPath)
    
    if 'water' not in fileList[0]: interval_95 = PercentileInterval(pngSretch)
    else: interval_95 = PercentileInterval(100)

    for filename in fileList:
        band = tiff.imread(dataPath / filename)
        if pngSretch: 
            band = (interval_95(band.squeeze()) * 255).astype(np.uint8)
        imsave(str(savePath / "{}.png".format(filename[:-4])), band)


def tif_multiBands2png_GDAL(dataPath, dataName, savePath, bandNameList, pngSretch):
    if not os.path.exists(savePath):
        os.makedirs(savePath)

    if 'water' not in dataName:
        interval_95 = PercentileInterval(pngSretch)
    else:
        interval_95 = PercentileInterval(100)

    raster = gdal.Open(
        str(dataPath / "{}.tif".format(dataName)))  # read data

    data = raster.ReadAsArray()#.squeeze()
    if len(data.shape) < 3: data = data[np.newaxis, ]
    # print(data.shape, "data shape")
    for i, band in enumerate((bandNameList)):
        if pngSretch:
            jpg_data = (interval_95(data[i, ]) * 255).astype(np.uint8)
        else:
            jpg_data = data[i, ]

        # print("jpg_data: ", jpg_data.shape)
        # print("{}".format(saveName))
        imsave(str(savePath / "{}.{}.png".format(dataName, band)), jpg_data)


def band2png(data, savePath, saveName, pngSretch):
    run = GRID()
    interval = PercentileInterval(pngSretch)

    # proj, geotrans, data = run.read_data(
    #     dataPath + dataName + ".tif")  # read data

    # print("data shape {}".format(data.shape))

    if len(data.shape) == 2:
        jpg_data = interval(data)

    if not os.path.exists(savePath):
        os.makedirs(savePath)
    print("{}".format(saveName))
    imsave(savePath + saveName + ".png", jpg_data)


def tifBand2biMap_GDAL(dataPath, dataName, savePath, saveName, TH):
    run = GRID()
    interval_100 = PercentileInterval(100.)

    proj, geotrans, data = run.read_data(
        dataPath + dataName + ".tif")  # read data

    # print("data shape {}".format(data.shape))

    if len(data.shape) == 2:
        # jpg_data = interval_100(data)
        data[np.where(data > TH)] = 1.0
        data[np.where(data <= TH)] = 0.0

    if not os.path.exists(savePath):
        os.makedirs(savePath)
    print("{}".format(saveName))
    imsave(savePath + saveName + ".png", data)


def bandsMerge2tif(dataPath, dataName, savePath, saveName, stretchFlag):
    run = GRID()

    bandNameList = []
    interval = PercentileInterval(99)

    print(dataPath / "{}*.tif".format(dataName))
    fileNameList = glob.glob(str(dataPath / "{}*.tif".format(dataName)))
    num = len(fileNameList)

    proj, geotrans, data = run.read_data(fileNameList[0])  # read data
    bandNameList.append(fileNameList[0].split(".")[1])
    if stretchFlag:
        data = interval(data)

    if 1 == num:
        DATA = data
    else:

        DATA = np.zeros([num, data.shape[0], data.shape[1]])
        DATA[0, ...] = data

        for i in range(1, num):
            _, _, data = run.read_data(fileNameList[i])  # read data
            bandNameList.append(fileNameList[i].split(".")[1])
            if stretchFlag:
                DATA[i, ...] = interval(data)
            else:
                DATA[i, ...] = data

    if not os.path.exists(savePath):
        os.makedirs(savePath)
    print("{}: {}".format(saveName, bandNameList))
    run.write_data(str(savePath / "{}.tif".format(saveName)), proj, geotrans, DATA, bandNameList)


def rainTif2rgb(dataPath, dataName, savePath, saveName, satName):
    if satName == 'noaa':
        maxRain = 718.62  # mm
    elif satName == 'chirps':
        maxRain = 1444.34  # mm
    else:
        maxRain = 1.0

    run = GRID()

    proj, geotrans, data = run.read_data(
        dataPath + dataName + ".tif")  # read data

    print("data shape {}".format(data.shape))

    if len(data.shape) == 3:
        data = data[0:3, :, :]
        jpg_data = data.transpose(1, 2, 0)

    if len(data.shape) == 2:
        # jpg_data = np.zeros([data.shape[0], data.shape[1], 3])
        # jpg_data[..., 0] = data
        # jpg_data[..., 1] = data
        # jpg_data[..., 2] = data
        # jpg_data = np.uint8(jpg_data *255)
        jpg_data = data / maxRain

    if not os.path.exists(savePath):
        os.makedirs(savePath)
    print("{}".format(saveName))
    imsave(savePath + saveName + ".png", jpg_data, cmap=plt.cm.Greens)


from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance


def lee_filter(img, size):
    img_mean = uniform_filter(img, (size, size))
    img_sqr_mean = uniform_filter(img ** 2, (size, size))
    img_variance = img_sqr_mean - img_mean ** 2

    overall_variance = variance(img)

    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)
    return img_output


# from pyradar.filters.lee import lee_filter
# from pyradar.filters.mean import mean_filter
# from pyradar.filters.median import median_filter
if __name__ == "__main__":
    dataPath = r"F:\Thomas_WildFire_SAR_MSI_100m_EPSG_32610_0721\Thomas_50m_HM_Coef_Tif_collection\\"
    savePath = dataPath + 'PNG\\'
    # os.mkdir(savePath)

    dataName = "harmonicCoef"

    bandList = ['constant', 't', 'cos_1', 'sin_1']
    for band in bandList:
        img, mask = read_tif_and_get_bands(dataPath, dataName, [band])
        img_scaled = interval_95(img.squeeze())

        if band in ['cos_1']:
            cos_1 = img.squeeze()
        if band in ['sin_1']:
            sin_1 = img.squeeze()

        # plt.imsave(savePath + "{}.{}.png".format(dataName, band), img_scaled, cmap='gray')

    rho = np.sqrt(pow(cos_1, 2) + pow(sin_1, 2))
    phase = np.arctan2(sin_1, cos_1)

    # plt.imsave(savePath + "{}.{}.png".format(dataName, 'rho'), interval_95(rho), cmap='gray')
    imsave(savePath + "{}.{}.png".format(dataName, 'phase'), interval_95(phase))

    # bandsMerge2tif(dataPath, dataName, savePath, dataName, stretchFlag=True)

    # raster = gdal.Open(dataPath + dataName + ".tif")  # open file

    # data = raster.ReadAsArray(0, 0)#[np.newaxis, ...]  # read data as array
    # mask = raster.GetRasterBand(1).GetMaskBand().ReadAsArray(0, 0)[np.newaxis, ...]/255

    # run = GRID()
    # sarPath = "F:\Camp_WildFire_SAR_20m_STD_V2_G21\Camp_20m_SAR_Tif_collection\\"
    # proj, geotrans, water = run.read_data(sarPath + "waterMask.tif")  # read data
    #
    # print(proj)
    #
    # # SAR, mask = read_tif_and_get_bands(dataPath, dataName, ['VV', 'VH', 'RBR'])
    # # print(SAR.shape)
    #
    # for band in ['VV', 'VH', 'RBR']:
    #     SAR, _ = read_tif_and_get_bands(dataPath, dataName, [band])
    #     SAR_scaled = interval_95(SAR.squeeze())
    #     plt.imsave(dataPath + "{}.{}.png".format(dataName, band), SAR_scaled, cmap = 'gray')
