from easydict import EasyDict as edict

# Wildfire Event
EVENT_SET = edict({

    'CA2017Elephant': {
        "name": "CA2017Elephant",
        "roi": [-121.7697, 50.6512, -120.7068, 51.5224],
        "year": 2017,
        'crs': "EPSG:32610",

        "modisStartDate": "2017-06-01",
        "modisEndDate": "2017-10-10",

        "where": 'CA'
    },

    "AU2020Fraser": {
        "name": "AU2020Fraser",
        "roi": [
            -207.034607,
            -25.495347,
            -206.603394,
            -24.666986
        ],
        "year": 2020,
        "crs": "EPSG:32756",

        "areaTH": 1000.0,
        "modisStartDate": "2020-09-01",
        "modisEndDate": "2020-12-31",
        "BIOME_NUM": 4,
        "BIOME_NAME": "Deserts & Xeric Shrublands",

        "where": 'AU'
    },

    'CA2021CrissCreek': {
        "name": "CA2021CrissCreek",
        "roi": [-121.25734721267986,50.77521426741906, 
                -120.45259867752361,51.37573515229082],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-06-01",
        "modisEndDate": "2021-08-30",

        "where": 'CA'
    },

    'US_2021_Dixie': {
        "name": "US_2021_Dixie",
        "roi": [-121.74353468872346,39.57045495653947, 
                -119.99670851684846,40.845718561586715],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-07-01",
        "modisEndDate": "2021-11-01",

        "orbKeyList": ['ASC137'],
        "orbNumList": [137],
        
        "where": 'US'
    },

    'CA_2021_Kamloops': {
        "name": "CA_2021_Kamloops",
        "roi": [-122.62367254555225,49.96628372458412, 
                -119.52552801430225,51.795919306523245],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-06-28",
        "modisEndDate": "2021-11-01",
    
        "dNBR_Flag": False,
        "S2_Master": "2021-07-01",
        
        "orbKeyList": ['ASC64', 'DSC13'],
        "orbNumList": [64, 13],

        "where": 'CA'
    }

    # "SE2018Ljusdals": {
    #     'name': 'SE2018Ljusdals', # Enskogen (A, C, F), 
    #     'roi': [15.137434283688016, 61.86566784664094,
    #             15.604353229000516, 62.06961520427164], # buffer(2000)
    #     'year': 2018,
    #     'crs': 'EPSG:32633',

    #     'modisStartDate': '2018-07-01',  # 2019-05-18
    #     'modisEndDate': '2018-08-20',  # 2019-10-01
        
    #     "where": 'SE'
    # }
})
