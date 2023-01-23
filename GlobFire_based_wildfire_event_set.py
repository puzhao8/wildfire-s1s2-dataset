
# This code was adapted from its GEE version entiled: GlobFire_Based_Wildfire_Dataset
# https://code.earthengine.google.com/fc583fbb90cf45516d544db809aedda5

from easydict import EasyDict as edict
from eo_class.fireEvent import save_fireEvent_to_json
from eo_class.fireEvent import get_local_crs_by_query_S2, FIREEVENT

import ee
ee.Initialize()

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

def poly_to_event(poly: ee.Feature) -> dict:
    ''' convert single polygon into an event dictionary
        return {
            'name': 'ID_xxxxxx_-1739E_23890N',
            'roi': [0, 0, 0, 0],
            'start_date': '2022-01-01',
            'end_date': '2022-01-01',
            ...
        }
    '''
    event = edict(poly.toDictionary().getInfo())
    roi =  ee.Feature(poly_list.get(0)).buffer(buffer_size).bounds().geometry()
    # event['crs'] = get_local_crs_by_query_S2(roi)

    # centroid coordinates
    centroid = roi.centroid(ee.ErrorMargin(500)).coordinates()
    longtitude = ee.Number(centroid.get(0)).multiply(1e3).round().int16()
    latitude = ee.Number(centroid.get(1)).multiply(1e3).round().int16()
    event['name'] = f"EU_{poly.get('year')}_ID_{poly.get('Id').getInfo()}_{longtitude.format().getInfo()}E_{latitude.format().getInfo()}N"

    coordinates = ee.List(roi.coordinates().get(0))
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
            [51.7530011817405, 71.20061603508908]]])


    ''' configuration '''
    # query region
    region = ee.FeatureCollection(EU)
    firePolys = (GWIS.filterBounds(region)
                    .filter(ee.Filter.gt("IDate", ee.Date("2017").millis()))
                    .filter(ee.Filter.lte("FDate", ee.Date("2018").millis()))
                    .map(add_property)
                    .filter(ee.Filter.gt("area_ha", 2000))
                    #   .merge(SWE)
                )
                
    poly_num = firePolys.size()
    poly_list = firePolys.toList(poly_num)


    buffer_size = 1e3 # expand wildfire roi

    EVENT_SET = {}
    for idx in range(10, 11):

        poly = ee.Feature(poly_list.get(idx))
        event = poly_to_event(poly)
        event.update({
            'modis_min_area': 1e2, # ignore small polygons for modis, 1e4
            'bufferSize': 1e4,
            })
        print(f'event name: {event.name}')

        fireEvent = FIREEVENT(event)
        fireEvent()

        # EVENT_SET.update({event.name: event})

    # save_fireEvent_to_json(EVENT_SET, "wildfire_events/EU_test.json")





    ''' display '''
    # # Map.addLayer(MGRS, {}, 'MGRS')
    # Map.centerObject(region, 3)
    # Map.addLayer(firePolys, {}, 'firePolys', false)
    # Map.addLayer(firePolys.style({color: 'red', fillColor: "#ff000000"}), {}, 'fire')
    # Map.addLayer(ee.FeatureCollection([firePolys.first()]), {}, 'firePolys-first')

    # Map.addLayer(country_bounds_map, {}, 'country_bounds_map', false)
    # Map.addLayer(region.style({color:'purple', fillColor:'#ff000000', width:1}), {}, 'country')