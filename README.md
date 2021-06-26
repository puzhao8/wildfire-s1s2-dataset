"# wildfire-s1s2-dataset" 

# wildfire-s1s2-dataset
- **data: SAR and MSI Data**
    - S1: 10m Sentinel-1 SAR Data (Fire Year: 2019)
        - ASC-pre (Before Year: 2018)
        - ASC-post (After Year: 2020)
        - DSC-pre (Before Year: 2018)
        - DSC-post (After Year: 2020)
    - S2: 10m/20m Sentinel-2 MSI Data
        - pre (Before Year: 2018)
        - post (After Year: 2020)
    - ALOS: 25m ALOS PALSAR L-Band
        - pre (Before Year: 2018)
        - post (After Year: 2020)
- **mask: Mask Data**
    - poly: Official Polygon in Raster (10m)
    - modis: MODIS Global Burned Area Product (500m)
    - viirs: VIIRS Global Active Fire (375m)
    - mtbs: MTBS (United States, 30m) 
    - water: Water Mask (CGLS-LC100: 100m)
- **auxiliary data**
    - DEM/DSM (ALOS World 3D - 30m (AW3D30))
    - Land Cover (NLCD-30m: USGS/NLCD_RELEASES/2016_REL/2016[_AK], Global CGLS-LC100: 100m)
    - Biome (RESOLVE Ecoregions 2017)
    - LIA: local incidence angle (TBD...)
    - Moisture: Precipitation (TBD...)
