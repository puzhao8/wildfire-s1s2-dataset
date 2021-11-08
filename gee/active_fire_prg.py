import ee
ee.Initialize()

from datetime import datetime

def get_daily_viirs_progression(prg_roi, start_date=None, end_date=None):
    base_AF_SUOMI_VIIRS = ee.FeatureCollection("users/omegazhangpzh/NRT_AF/SUOMI_VIIRS_C2_Global_Archived_2021")
    base_AF_J1_VIIRS = ee.FeatureCollection("users/omegazhangpzh/NRT_AF/SUOMI_VIIRS_C2_Global_Archived_2021")
    AF_BASE = base_AF_SUOMI_VIIRS.merge(base_AF_J1_VIIRS)

    # AF_SUOMI_VIIRS = ee.FeatureCollection("users/omegazhangpzh/NRT_AF/SUOMI_VIIRS_C2_Global_7d")
    # AF_J1_VIIRS = ee.FeatureCollection("users/omegazhangpzh/NRT_AF/J1_VIIRS_C2_Global_7d")
    # AF_MODIS = ee.FeatureCollection("users/omegazhangpzh/NRT_AF/MODIS_C6_1_Global_7d")
        
    def set_buffer(pnt): return pnt.buffer(ee.Number(375).divide(2)).bounds()
    def set_julian_day(pnt): return pnt.set("julian_day", ee.Date(pnt.get("ACQ_DATE")).getRelative('day', 'year'))

    viirs_af = (AF_BASE.filterBounds(prg_roi)
                        .map(set_julian_day)
                )
                    
    #   // print("before filtering: " + viirs_af.size().getInfo())
    if start_date is None: start_date = "2021-05-01"
    if end_date is None: end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S").split("T")[0]
    viirs_af = (viirs_af
                    .filter(ee.Filter.gte("julian_day", ee.Date(start_date).getRelative('day', 'year')))
                    .filter(ee.Filter.lte("julian_day", ee.Date(end_date).getRelative('day', 'year')))
                )
    #   // print("after filtering: " + viirs_af.size().getInfo())     
                        
    min_max = viirs_af.reduceColumns(ee.Reducer.percentile([2, 98], ['min', 'max']), ['julian_day'])
    min = min_max.get('min').getInfo()
    max = min_max.get('max').getInfo()
                        
    viirs_prg = viirs_af.map(set_buffer).reduceToImage(["julian_day"], ee.Reducer.first()).rename('prg')
    viirs_prg = ee.Image(viirs_prg.setMulti({'min': min, 'max': max}))

    return viirs_prg