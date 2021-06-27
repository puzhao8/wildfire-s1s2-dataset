
from prettyprinter import pprint
from easydict import EasyDict as edict
import ee
ee.Initialize()


cfg = edict()

# Wildfire Event
event = edict({
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
    "modisStartDate": "2020-10-10",
    "modisEndDate": "2020-12-09",
    "BIOME_NUM": 4,
    "BIOME_NAME": "Deserts & Xeric Shrublands",

    "where": 'AU'
})


event['start_date'] = event['modisStartDate']
event['end_date'] = event['modisEndDate']
event['year'] = ee.Number(event['year']).format().getInfo()
event['roi'] = ee.Geometry.Rectangle(event['roi']).getInfo()['coordinates'][0]

pprint(event['roi'])

# Query Progression and Export 
from gee.progression import query_progression_and_export
print(f"-----------------> {event.name} <------------------ ")
query_progression_and_export(cfg, event, scale=100, BUCKET="wildfire-prg-dataset", export_sat=['mask'])