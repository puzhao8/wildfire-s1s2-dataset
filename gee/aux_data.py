
import ee
ee.Initialize()

from easydict import EasyDict as edict


""" #################################################################
Query Auxiliary Data
################################################################# """ 
def get_aux_dict():
    aux_dict = edict()

    """ Land Cover """
    # land_cover_2017 = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017")
    # landcover = land_cover_2017.select("discrete_classification").rename('landcover')

    # WorldCover
    worldCover = ee.ImageCollection("ESA/WorldCover/v100").mosaic().rename('landcover')
    aux_dict['landcover'] = worldCover


    """DEM"""
    # # ALOS DSM: Global 30m
    # dataset = ee.ImageCollection('JAXA/ALOS/AW3D30/V3_2')
    # elevation_org = dataset.select('DSM')
    # proj = elevation_org.first().select(0).projection()
    # elevation = elevation_org.mosaic().setDefaultProjection(proj).select('DSM').rename('elevation')

    # FABDEM (Forest And Buildings removed Copernicus 30m DEM)
    fabdem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM")
    elevation = fabdem.mosaic().rename('elevation').setDefaultProjection('EPSG:3857', None, 30)
    aux_dict['DEM'] = ee.Terrain.products(elevation)

    # # NASADEM: NASA NASADEM Digital Elevation 30m [-60 ~ 60]
    # STRM = ee.Image("NASA/NASADEM_HGT/001")
    # DEM = ee.Terrain.products(STRM.select('elevation'))


    # Biome
    ### Climate Zone ###
    ecoRegions = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
    eco_palette = ecoRegions.aggregate_array("COLOR_BIO").distinct()
    eco_names = ecoRegions.aggregate_array("BIOME_NAME").distinct()

    biomeRegions = ecoRegions.setMulti({
        'palette': eco_palette,
        'names': eco_names 
    })

    biomeImg = ee.FeatureCollection(biomeRegions).reduceToImage(['BIOME_NUM'], ee.Reducer.first()).rename("BIOME_NUM")
    aux_dict['biome'] = biomeImg

    return aux_dict


