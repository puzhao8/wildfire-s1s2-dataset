
import ee

def unionGeomFun(img, first):
    rightGeo = ee.Geometry(img.geometry())
    return ee.Geometry(first).union(rightGeo)

""" Sentinel-2 MSI Data """
def set_group_index_4_S2(img, groupLevel='day'):

    group_dict = {
        'month': 7,
        'day': 10,
        'hour': 13,
        'minute': 16,
        'second': 19
    }
        
    imgDateStr = img.date().format()
    groupIndex = imgDateStr.slice(0, group_dict[groupLevel])  # 2017-07-23T14:11:22(len: 19)

    date = (imgDateStr.slice(0, group_dict[groupLevel])
            .replace('-', '').replace('-', '').replace(':', '').replace(':', ''))

    imgLabel = date.cat(f"_S2")

    return img.setMulti({
        'GROUP_INDEX': groupIndex,
        'SAT_NAME': "S2",
        'IMG_LABEL': imgLabel
    })

# "group by date
def group_MSI_ImgCol(imgcollection, groupLevel='day', multiSensorGroupFlag=False):
    
    imgCol_sort = imgcollection.sort("system:time_start")
    imgCol = imgCol_sort.map(lambda img: set_group_index_4_S2(img, groupLevel))

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

    org_proj = ee.Image(ji.first()).select(0).projection()
    propertyList = ['GROUP_INDEX', 'system:time_start', 'IMG_LABEL']

    def mosaicImageBydate(img):
        imgCol2mosaic = ee.ImageCollection.fromImages(img.get('to_mosaic'))
        mosaicGeom = imgCol2mosaic.geometry().dissolve(ee.ErrorMargin(100, 'meters'))
        mosaiced = ee.Image(imgCol2mosaic.mosaic().copyProperties(img, propertyList))
        return ee.Image(
            mosaiced.set("system:footprint", mosaicGeom)
                # .set('system:time_start', mosaiced.date().format("Y-MM-01")) # first day of month
                .setDefaultProjection(crs=org_proj)
        )

    imgcollection_grouped = ji.map(mosaicImageBydate)
    return ee.ImageCollection(imgcollection_grouped.copyProperties(imgCol, imgCol.propertyNames()))



""" Sentinel-1 SAR Data """
def set_group_index_4_S1(img, groupLevel=13, labelShowLevel=13):
    orbitKey = (ee.String(img.get("orbitProperties_pass")).replace('DESCENDING', 'DSC').replace('ASCENDING', 'ASC')
                .cat(ee.Number(img.get("relativeOrbitNumber_start")).int().format()))
    Date = (img.date().format().slice(0, labelShowLevel)
                .replace('-', '').replace('-', '').replace(':', '').replace(':', ''))
    Name = (Date).cat('_').cat(orbitKey)

    groupIndex = img.date().format().slice(0, groupLevel)  # 2017 - 07 - 23T14:11:22(len: 19)
    return img.setMulti({
        'GROUP_INDEX': groupIndex,
        'IMG_LABEL': Name,
        'Orbit_Key': orbitKey
    })


# "group by" date
def group_S1_by_date_orbit(imgcollection):
    imgCol_sort = imgcollection.sort("system:time_start")
    imgCol = imgCol_sort.map(set_group_index_4_S1)
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
        imgCol2mosaic = ee.ImageCollection.fromImages(img.get('to_mosaic'))
        mosaicGeom = imgCol2mosaic.geometry().dissolve()
        mosaiced = imgCol2mosaic.mosaic().copyProperties(img, img.propertyNames())
        return ee.Image(mosaiced).set("system:footprint", mosaicGeom) 

    imgcollection_grouped = ji.map(mosaicImageBydate)
    return ee.ImageCollection(imgcollection_grouped.copyProperties(imgCol, imgCol.propertyNames()))