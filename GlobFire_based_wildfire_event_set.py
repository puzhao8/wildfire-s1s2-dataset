
# This code was adapted from its GEE version entiled: GlobFire_Based_Wildfire_Dataset
# https://code.earthengine.google.com/fc583fbb90cf45516d544db809aedda5

from easydict import EasyDict as edict
from eo_class.fireEvent import save_fireEvent_to_json
from eo_class.fireEvent import get_local_crs_by_query_S2, FIREEVENT

import ee
ee.Initialize()

import time

def add_property(poly):
    ''' add specific properties including 
        'year': 2022,
        'area_ha': 2000, # the size of burned areas in hectare (poly)
    '''
    year = ee.Number.parse(ee.Date(poly.get("IDate")).format().slice(0,4))
    # area_ha = ee.Algorithms.If(poly.propertyNames().contains('area'), ee.Number(poly.get("area")).multiply(1e-4), 0)
    # area_ha = poly.bounds(ee.ErrorMargin(1e3)).area(ee.ErrorMargin(1e3))
    area_ha = poly.geometry().area(ee.ErrorMargin(100)).multiply(1e-4).round()
    return poly.set("year", year).set('area_ha', area_ha)

def poly_to_event(poly: ee.Feature, buffer_size: int=2e3, region: str='EU') -> dict:
    ''' convert single polygon into an event dictionary
        return {
            'name': 'ID_xxxxxx_-1739E_23890N',
            'roi': [0, 0, 0, 0],
            'start_date': '2022-01-01',
            'end_date': '2022-01-01',
            ...
        }
    '''

    roi =  ee.Feature(poly).buffer(buffer_size).bounds().geometry()
    coordinates = ee.List(roi.coordinates().get(0))

    event = edict(poly.toDictionary().getInfo())

    # event['crs'] = get_local_crs_by_query_S2(roi)

    # centroid coordinates
    # centroid = ee.List(roi.centroid(ee.ErrorMargin(500)).coordinates())
    centroid = ee.List(coordinates.get(0))
    longtitude = ee.Number(centroid.get(0)).multiply(1e3).round().format().slice(0, -2)
    latitude = ee.Number(centroid.get(1)).multiply(1e3).round().format().slice(0, -2)
    event['name'] = ee.String(f'{region}_').cat(ee.Number(poly.get('year')).format())\
            .cat("_ID_").cat(ee.Number(poly.get('Id')).format())\
                .cat('_').cat(longtitude).cat('E_').cat(latitude).cat('N')\
                    .getInfo()

    # event['name'] = f"EU_{poly.get('Id').getInfo()}"
    # event['name'] = f"EU_{poly.get('year').getInfo()}_ID_{poly.get('Id').getInfo()}_{longtitude.format().getInfo()}E_{latitude.format().getInfo()}N"

    event['roi'] = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()

    event['start_date'] = ee.Date(poly.get('IDate')).format().slice(0, 10).getInfo()
    event['end_date'] = ee.Date(poly.get('FDate')).format().slice(0, 10).getInfo()

    return event


if __name__ == "__main__":

    # wildfire polygon dataset
    GWIS = ee.FeatureCollection("JRC/GWIS/GlobFire/v2/FinalPerimeters")
    SWE = ee.FeatureCollection("users/omegazhangpzh/Sweden_Largest_10_burntArea_2018")

    # country boundaries
    country_bounds = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
    country = country_bounds.filter(ee.Filter.stringContains("ADM0_NAME", 'Spain')).union(ee.ErrorMargin(500))
    # print("country_flt", country.limit(10))

    EU = ee.Geometry.Polygon(
            [[[-14.516530068259499, 71.20061603508908],
            [-14.516530068259499, 34.04930741835553],
            [51.7530011817405, 34.04930741835553],
            [51.7530011817405, 71.20061603508908]]], None, False)
    
    # Russia
    RU = ee.Geometry.Polygon(
        [[[67.50924333961639, 77.9174373628489],
          [67.50924333961639, 51.51399986909121],
          [190.20455583961643, 51.51399986909121],
          [190.20455583961643, 77.9174373628489]]], None, False)

    REGION = {'EU': EU, 'RU': RU}

    def create_wildfire_events_based_on_GlobFire(region:str='EU', year:int=2017, export_flag:bool=True):
        # query region
        firePolys = (GWIS.filterBounds(REGION[region])
                        .filter(ee.Filter.gte("IDate", ee.Date(str(year)).millis()))
                        .filter(ee.Filter.lt("IDate", ee.Date(str(year+1)).millis()))
                        .map(add_property)
                        .filter(ee.Filter.gt("area_ha", 2000))
                        #   .merge(SWE)
                    )
                    
        poly_num = firePolys.size()
        poly_list = ee.List(firePolys.toList(poly_num))
        print(f"Total number of fire events in {year}: {poly_num.getInfo()}")

        if export_flag:
            EVENT_SET = {}
            for idx in range(1, poly_num.getInfo()):
                print(f"------------------ idx: {idx} ----------------------")

                poly = ee.Feature(poly_list.get(idx)) # get(idx)
                area = float(poly.get('area_ha').getInfo())
                if(area < 1e10): # remove anamoly polygon by area_ha property
                    # event = poly_to_event(poly=poly, buffer_size=2e3, region=region)

                    time_start = time.time()

                    roi =  ee.Feature(poly).buffer(2e3).bounds().geometry()
                    coordinates = ee.List(roi.coordinates().get(0))

                    print("Elapsed time before toDict: {:.2f} seconds".format(time.time() - time_start))
                    event = edict(poly.toDictionary().getInfo())
                    print("Elapsed time after toDict: {:.2f} seconds".format(time.time() - time_start))

                    event['roi'] = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()
                    print("Elapsed time after roi: {:.2f} seconds".format(time.time() - time_start))

                    event.update({
                            'name': ee.String('Event_ID_').cat(ee.Number(poly.get('Id')).format()).getInfo(),
                            'buffer_size': int(2e3)
                        })

                    print(f'event: {event.name}')
                    print(f'area: {area}')

                    print("Elapsed time: {:.2f} seconds".format(time.time() - time_start))

                    # update roi, add crs, BIOME_NUM, BIOME_NAME etc.
                    fireEvent = FIREEVENT(country=region, **event)
                    event = fireEvent.query_modis_fireEvent_info(event=event, save_flag=True, save_url=f"wildfire_events/GlobFire_EU_exported.json")

                    EVENT_SET.update({event.name: event})
                    save_fireEvent_to_json(EVENT_SET, f"wildfire_events/GlobFire_{region}_{year}_events_TEST.json")

                else:
                    print("Too large polygon !!!", poly.get('area_ha').getInfo())


    ''' configuration '''
    for region in ['RU']:
        for year in range(2017, 2022):
            create_wildfire_events_based_on_GlobFire(region, year, True)