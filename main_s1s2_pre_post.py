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

json_dict = {
    'AK': "./wildfire_events/MTBS_AK_2017_2019_events_ROI.json",
    'US': "./wildfire_events/MTBS_US_2017_2019_events_ROI.json",
    'CA_2017': "./wildfire_events/POLY_CA_2017_events_gt2k.json", # "minBurnArea": 2000
    'CA_2018': "./wildfire_events/POLY_CA_2018_events_gt2k.json",
    'CA_2019': "./wildfire_events/POLY_CA_2019_events_gt2k.json",
}

""" CFG """
cfg = edict({
    'where': 'CA_2019', # 'US,
    'minBurnArea': 2000,

    # # AK
    # "period": 'fire_period', #'fire_period', # "season" for AK only?
    # "season": [-1, 2], # [-1, 2] means last Dec. to this Feb, this is for AK.

    # Canada
    "period": 'season', #'fire_period', # "season" for AK only?
    "season": [5, 8], # [-1, 2] means last Dec. to this Feb, this is for CA.

})

cfg['JSON'] = json_dict[cfg.where]

""" #################################################################
Wildfire Event
################################################################# """ 
from eo_class.fireEvent import load_json
from gee.export import query_s1s2_and_export


print(cfg.JSON)
EVENT_SET = load_json(cfg.JSON)

EVENT_SET_subset = edict()
for event_id in EVENT_SET.keys():
    if cfg['where'] in ['AK', 'US']:
        if EVENT_SET[event_id]["BurnBndAc"] >= cfg.minBurnArea:
            EVENT_SET_subset.update({event_id: EVENT_SET[event_id]})

    if cfg['where'] in ['CA_2017', 'CA_2018', 'CA_2019']:
        if EVENT_SET[event_id]["ADJ_HA"] >= cfg.minBurnArea:
            EVENT_SET_subset.update({event_id: EVENT_SET[event_id]})

print("\n\n==========> wildfire-s1s2-dataset <=========")
num = len(EVENT_SET_subset)
print(f"total number of events to query: {num} \n")

# LOOP HERE
# event = EVENT_SET['al3107008672320170117']
# idx_stop = list(EVENT_SET_subset.keys()).index("CA_BC_1157_2017")
# print(f"idx_stop: {idx_stop}")

for event_id in list(EVENT_SET_subset.keys()) : #EVENT_SET_subset.keys(): #: # [idx_stop:] 
    
    event = EVENT_SET[event_id]
    event['where'] = cfg['where']

    if event['where'] in ['AK', 'US']:
        event['start_date'] = event['Ig_Date']
        event['end_date'] = event['modisEndDate']
        event['year'] = ee.Number(event['YEAR']).format().getInfo()
        # pprint(event)

    if event['where'] in ['CA_2017', 'CA_2018', 'CA_2019']:
        event['start_date'] = event['modisStartDate'] or event["AFSDATE"] or event['SDATE']
        event['end_date'] = event['modisEndDate'] or event["AFEDATE"] or event['EDATE']
        event['year'] = ee.Number(event['YEAR']).format().getInfo()

        event['name'] = event['NAME']

        # tmp = event['NAME'].split("_")
        # event['name'] = f"{tmp[0]}_{tmp[-1]}_{tmp[1]}_{tmp[2]}"

    if event['where'] in ['EU']:
        pass

    print(f"-----------------> {event.name} <------------------ ")
    query_s1s2_and_export(cfg, event, 
            scale=20, 
            BUCKET="wildfire-s1s2-dataset-ca-2019-median",
            # export=['S2']
            export=['S2', 'S1', 'ALOS', 'mask', 'AUZ']
        )