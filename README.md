"# wildfire-s1s2-dataset" 
# create python evnironment
``` shell
conda env create -f environment.yaml
```

# export multi-source data, such as Sentinel-1/2 and ALOS
``` shell
python main_s1s2_pre_post.py
```

# export modis/viirs data
``` shell
python main_s1s2_modis_viirs_export.py
```

# prepare event database into json
``` shell
python main_4_gen_[CA]_fireEvent_json.py
```

# wildfire-s1s2-dataset
- **data: SAR and MSI Data**
    - S1: 10m Sentinel-1 SAR Data (Fire Year: 2019)
        - pre (Before Year: 2018, mean)
            - event1_ASC36.tif
            - event1_DSC36.tif
            - event2_ASC17.tif
        - post (After Year: 2020, mean)
            - event1_ASC36.tif
            - event1_DSC36.tif
            - event2_ASC17.tif
    - S2: 10m/20m Sentinel-2 MSI Data
        - pre (Before Year: 2018, median)
            - event1.tif
            - event2.tif
        - post (After Year: 2020, median)
            - event1.tif
            - event2.tif
    - ALOS: 25m ALOS PALSAR L-Band
        - pre (Before Year: 2018)
            - event1.tif
            - event2.tif
        - post (After Year: 2020)
            - event1.tif
            - event2.tif
    - MODIS: 250m & 500m Daily (SR)
        - post 
            - event1.tif
            - event2.tif
        - progression
            - event1
                - 2022-06-01.tif
                - 2022-06-02.tif
            - event2
                - 2022-06-10.tif
                - 2022-06-11.tif

- **mask: Mask Data**
    - poly: Official Polygon in Raster (10m)
        - event1.tif
        - event2.tif
    - firecci: FIRECCI Global Burned Area Product (250m)
    - modis: MODIS Global Burned Area Product (500m)
    - viirs: VIIRS Global Active Fire (375m, TBD...)
    - mtbs: MTBS (United States, 30m) 
- **auxiliary data**
    - DEM/DSM (ALOS World 3D - 30m (AW3D30))
    - Land Cover (NLCD-30m: USGS/NLCD_RELEASES/2016_REL/2016[_AK], Global CGLS-LC100: 100m)
    - Biome (RESOLVE Ecoregions 2017)
    - water: Water Mask (CGLS-LC100: 100m)
    - LIA: local incidence angle (TBD...)
    - Moisture: Precipitation (TBD...)
