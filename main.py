import os
from pathlib import Path 
from easydict import EasyDict as edict
from prettyprinter import pprint

import logging
logger = logging.getLogger(__name__)

from typing import Dict
import ee
ee.Initialize()


# from eo_class.modisPoly import MODIS_POLY
import yaml
import numpy as np
import json

""" CFG """
cfg = edict({
    'where': 'AK', # 'US,
    "JSON": "G:\PyProjects\wildfire-s1s2-dataset\wildfire_events\MTBS_AK_2017_2019_events_ROI.json",
    "period": 'fire_period', # "season"
    "season": [-1, 2],
})


""" #################################################################
Wildfire Event
################################################################# """ 
from eo_class.fireEvent import load_json
from gee.export import query_s1s2_and_export


print(cfg.JSON)
EVENT_SET = load_json(cfg.JSON)

EVENT_SET_subset = edict()
for event_id in EVENT_SET.keys():
    if EVENT_SET[event_id]["BurnBndAc"] > 1000:
        EVENT_SET_subset.update({event_id: EVENT_SET[event_id]})

print("\n\n==========> wildfire-s1s2-dataset <=========\n")
print(f"total number of events to query: {len(EVENT_SET_subset)}")

# LOOP HERE
# event = EVENT_SET['al3107008672320170117']
for event_id in ["ak6524416010220190610"]: # EVENT_SET_subset.keys():
    
    event = EVENT_SET[event_id]
    event['where'] = cfg['where']

    if event['where'] in ['AK', 'US']:
        event['start_date'] = event['Ig_Date']
        event['end_date'] = event['modisEndDate']
        event['year'] = ee.Number(event['YEAR']).format().getInfo()
        # pprint(event)

    if event['where'] in ['CA']:
        pass

    if event['where'] in ['EU']:
        pass

    query_s1s2_and_export(cfg, event, scale=20, BUCKET="wildfire-s1s2-dataset-v1", export_sat=['S2'])

