
# from main import EVENT_SET
from prettyprinter import pprint
from easydict import EasyDict as edict
import ee
ee.Initialize()


cfg = edict({
    "roi_cloud_level": 30,
    "filter_by_cloud": True,
    "S2_BANDS": ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'],
    "extend_months": 0, # 1
})

# Wildfire Event
EVENT_SET = edict({

    'CA2017Elephant': {
        "name": "CA2017Elephant",
        "roi": [-121.7697, 50.6512, -120.7068, 51.5224],
        "year": 2017,
        'crs': "EPSG:32610",

        "modisStartDate": "2017-06-01",
        "modisEndDate": "2017-10-10",

        "where": 'CA'
    },

    "AU2020Fraser": {
        "name": "AU2020Fraser",
        "roi": [
            -207.034607,
            -25.495347,
            -206.603394,
            -24.666986
        ],
        "year": 2020,
        "crs": "EPSG:32756",

        "areaTH": 1000.0,
        "modisStartDate": "2020-09-01",
        "modisEndDate": "2020-12-31",
        "BIOME_NUM": 4,
        "BIOME_NAME": "Deserts & Xeric Shrublands",

        "where": 'AU'
    },

    'CA2021CrissCreek': {
        "name": "CA2021CrissCreek",
        "roi": [-121.25734721267986,50.77521426741906, 
                -120.45259867752361,51.37573515229082],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-06-01",
        "modisEndDate": "2021-08-30",

        "where": 'CA'
    },

    # "SE2018Ljusdals": {
    #     'name': 'SE2018Ljusdals', # Enskogen (A, C, F), 
    #     'roi': [15.137434283688016, 61.86566784664094,
    #             15.604353229000516, 62.06961520427164], # buffer(2000)
    #     'year': 2018,
    #     'crs': 'EPSG:32633',

    #     'modisStartDate': '2018-07-01',  # 2019-05-18
    #     'modisEndDate': '2018-08-20',  # 2019-10-01
        
    #     "where": 'SE'
    # }
})


# event = EVENT_SET['CA2017Elephant']

for name in ['CA2021CrissCreek']: # list(EVENT_SET.keys())[:1]:
    event = EVENT_SET[name]

    event['start_date'] = event['modisStartDate']
    event['end_date'] = event['modisEndDate']
    event['year'] = ee.Number(event['year']).format().getInfo()
    event['roi'] = ee.Geometry.Rectangle(event['roi']).getInfo()['coordinates'][0]

    # pprint(event['roi'])

    # Query Progression and Export 
    from gee.progression import query_progression_and_export
    print(f"-----------------> {event.name} <------------------ ")

    query_progression_and_export(
        cfg, 
        event, 
        scale=20, 
        BUCKET="wildfire-prg-dataset-v1", 
        # export_sat=['mask'],
        export_sat=['mask', 'AUZ', 'S2']
    )