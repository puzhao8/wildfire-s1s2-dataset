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


# save wildfire events to json
def save_edict_to_json(event: edict, json_url: str) -> None:
    ''' write a dictionary object into a json file specified by the second parameter '''
    with open(json_url, 'w') as fp:
        json.dump(edict(event), fp, ensure_ascii=False, indent=4)

json_dict = {
    'AK': "./wildfire_events/MTBS_AK_2017_2019_events_ROI.json",
    'US': "./wildfire_events/MTBS_US_2017_2019_events_ROI.json",
    'CA_2017': "./wildfire_events/POLY_CA_2017_events_gt2k.json", # "minBurnArea": 2000
    'CA_2018': "./wildfire_events/POLY_CA_2018_events_gt2k.json",
    'CA_2019': "./wildfire_events/POLY_CA_2019_events_gt2k.json",
    'CA_2020': "./wildfire_events_final/Canada_Wildfires_2020.json",
    'CA_2021': "./wildfire_events_final/Canada_Wildfires_2021.json",
}

""" CFG """
cfg = edict({
    'where': 'CA_2020', # 'US,
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
from gee.export import update_query_event, query_s1s2_and_export, query_modis_viirs_and_export


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
# idx_stop = list(EVENT_SET_subset.keys()).index("CA_2019_ON_733")
# print(f"idx_stop: {idx_stop}")
# for event_id in list(EVENT_SET_subset.keys())[idx_stop:]: #list(EVENT_SET_subset.keys()): #: # [idx_stop:] 

ALL_EVENTS = edict()
fp = open(f"/Users/puzhao/PyProjects/wildfire-s1s2-dataset/wildfire_events_final/Canada_Wildfires_2020_modis.json", 'w')
for event_id in sorted(list(EVENT_SET_subset.keys())): #list(EVENT_SET_subset.keys()): #: # [idx_stop:] 
    
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
    
    if event['end_date'] is not None:
        print(f"-----------------> {event.name} <------------------ ")

        # # Sentinel-1, Sentinel-2
        # query_s1s2_and_export(queryEvent, 
        #         scale=20, 
        #         BUCKET="wildfire-dataset",
        #         dataset_folder=dataset_folder,
        #         export=['S2'],
        #         # export=['S2', 'S1', 'ALOS', 'mask', 'AUZ']
        #     )

        # modis and mask: https://code.earthengine.google.com/13d3c13ebb7b6b1ffe3bb461b60d2b30 (check exported data)
        modis_cloud_free_date = query_modis_viirs_and_export(queryEvent, 
                                    scale=250, 
                                    BUCKET="wildfire-dataset", 
                                    dataset_folder="wildfire-dataset-modis-s2-ak",
                                    export_mask=False)

        ''' export final roi '''
        coordinates = ee.List(queryEvent.roi.coordinates().get(0))
        event['roi'] = ee.List(coordinates.get(0)).cat(coordinates.get(2)).getInfo()
        event['modis_cloud_free_date'] = modis_cloud_free_date.getInfo()
        ALL_EVENTS.update({event.name: event})

    else:
        print(f"-----------------> {event.name}: end date is None <------------------ ")

    # save_edict_to_json(NEW_EVENT_SET, f"/Users/puzhao/PyProjects/wildfire-s1s2-dataset/wildfire_events_final/{cfg.where}.json")

json.dump(ALL_EVENTS, fp, ensure_ascii=False, indent=4)