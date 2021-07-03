
from prettyprinter import pprint
from easydict import EasyDict as edict
import ee
ee.Initialize()


cfg = edict()

# Wildfire Event
event = edict({
    "name": "George_Road",
    "roi": [
                [
                -121.66647924559321,
                50.094511029088174
                ],
                [
                -121.35336889403071,
                50.094511029088174
                ],
                [
                -121.35336889403071,
                50.28662256515625
                ],
                [
                -121.66647924559321,
                50.28662256515625
                ],
                [
                -121.66647924559321,
                50.094511029088174
                ]
            ],
    "year": 2021,
    "crs": "EPSG:32610",
    "areaTH": 2000.0,
    "modisStartDate": "2021-06-15",
    "modisEndDate": "2022-12-09",
    "BIOME_NUM": 4,
    "BIOME_NAME": "Deserts & Xeric Shrublands",

    "where": 'CA'
})


event['start_date'] = event['modisStartDate']
event['end_date'] = event['modisEndDate']
event['year'] = ee.Number(event['year']).format().getInfo()
# event['roi'] = ee.Geometry.Rectangle(event['roi']).getInfo()['coordinates'][0]

pprint(event['roi'])

# Query Progression and Export 
from gee.progression import query_progression_and_export
print(f"-----------------> {event.name} <------------------ ")
query_progression_and_export(cfg, event, scale=20, BUCKET="wildfire-prg-dataset", export_sat=['S2'])