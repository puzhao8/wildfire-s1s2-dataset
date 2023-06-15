
from eo_class.CA_fireEvent import FIREEVENT
from easydict import EasyDict as edict

cfg = edict({
        'COUNTRY': 'CA',
        # 'YEAR': 2019,
        'ADJ_HA_TH': 2e3, # 2e4, burned areas
        'modis_min_area': 1e2, # ignore small polygons for modis, 1e4
        'bufferSize': 1e4,
        # 'yml_url': 'CA_2017_Wildfire_V1.yaml'
    })

for YEAR in range(2020, 2022):
    cfg.YEAR = YEAR

    fireEvents = FIREEVENT(cfg)
    fireEvents()