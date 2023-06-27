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
    # United States
    'AK_2017_2019': "./wildfire_events/MTBS_AK_2017_2019_events_ROI.json",
    'US_2017_2019': "./wildfire_events/MTBS_US_2017_2019_events_ROI.json",
    'US_2020': "./wildfire_events/MTBS_US_2020_events.json",
    'US_2021': "./wildfire_events/MTBS_US_2021_events.json",

    # Canada 2017-2021
    'CA_2017': "./wildfire_events_final/Canada_Wildfires_2017.json", # "minBurnArea": 2000
    'CA_2018': "./wildfire_events_final/Canada_Wildfires_2018.json",
    'CA_2019': "./wildfire_events_final/Canada_Wildfires_2019.json",
    'CA_2020': "./wildfire_events_final/Canada_Wildfires_2020.json",
    'CA_2021': "./wildfire_events_final/Canada_Wildfires_2021.json"

    # GlobFire

}

""" CFG """
cfg = edict({
    # make changes here
    'where': 'CA_2021', # region and year
    'dataset_folder': "wildfire-s1s2-dataset-ca-2021", # folder in GCS bucket
    
    # setting for export
    'BUCKET': "wildfire-dataset", # GCS bucket
    'scale': 20, # spatial resolution
    'export': ['S2', 'S1', 'ALOS', 'mask', 'AUZ'], # export list

    'minBurnArea': 2000, # minimum burned areas being take as an event

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
from gee.export import update_query_event, query_s1s2_and_export, query_modis_and_export


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

# # LOOP HERE
# # # event = EVENT_SET['al3107008672320170117']
# idx_stop = list(EVENT_SET_subset.keys()).index("CA_2017_BC_990")
# print(f"idx_stop: {idx_stop}")
# for event_id in list(EVENT_SET_subset.keys())[idx_stop:idx_stop+1]: #list(EVENT_SET_subset.keys()): #: # [idx_stop:] 

''' Loop over each wildfire event '''
for event_id in list(EVENT_SET_subset.keys()): #list(EVENT_SET_subset.keys()): #: # [idx_stop:] 
    
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

    # # added on Nov-24-2021
    # if event.start_date is None: event['start_date'] = f"{event['YEAR']}-06-01"
    # if event.end_date is None: event['end_date'] = f"{event['YEAR']}-09-01"

    queryEvent = update_query_event(cfg, event)
    
    if ('end_date' in event.keys()):
        print(f"-----------------> {event.name} <------------------ ")

        # Sentinel-1, Sentinel-2
        query_s1s2_and_export(queryEvent, 
                scale=cfg.scale, 
                BUCKET=cfg.BUCKET,
                dataset_folder=cfg.dataset_folder,
                export=cfg.export
            )
