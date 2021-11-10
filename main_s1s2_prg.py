
# from main import EVENT_SET
from prettyprinter import pprint
from easydict import EasyDict as edict
import ee
ee.Initialize()

from wildfire_events.prg_events import EVENT_SET

cfg = edict({
    "roi_cloud_level": 5,
    "filter_by_cloud": False,
    "S2_BANDS": ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'],
    "extend_months": 1, # 1

    "pntsFilterFlag": False,
})

pprint(cfg)

# event = EVENT_SET['CA2017Elephant']

for name in ['CA_2021_Kamloops', 'US_2021_Dixie']: # list(EVENT_SET.keys())[:1]:
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
        export_sat=['S1', 'mask']
        # export_sat=['mask', 'AUZ', 'S1', 'S2']
    )