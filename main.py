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

# LOOP HERE
# event = EVENT_SET['ak6569814836520190622']
for event_id in EVENT_SET.keys():
    
    event = EVENT_SET[event_id]
    event['where'] = 'AK' # 'US

    if event['where'] in ['AK', 'US']:
        event['start_date'] = event['Ig_Date']
        event['end_date'] = event['modisEndDate']
        event['year'] = ee.Number(event['YEAR']).format().getInfo()
        # pprint(event)

    if event['where'] in ['CA']:
        pass

    if event['where'] in ['EU']:
        pass

    query_s1s2_and_export(cfg, event, scale=100, BUCKET="wildfire-s1s2-dataset", export_sat=['S2'])

