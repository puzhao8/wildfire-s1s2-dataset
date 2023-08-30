# from main import EVENT_SET
from prettyprinter import pprint
from easydict import EasyDict as edict
import ee
service_account = 'gee-login@ee-vishalned.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, '../ee-vishalned-455e271a521c.json')
ee.Initialize(credentials)
# ee.Initialize()


def get_pntsFilter(roi, buffer_size=0):
    ## ==> Point Filters <==
    pnt_roi = roi.buffer(buffer_size, ee.ErrorMargin(1)).bounds()
    coordList = ee.List(pnt_roi.coordinates().get(0))
    btmLeft = ee.Geometry.Point(coordList.get(0))
    btmRight = ee.Geometry.Point(coordList.get(1))
    topRight = ee.Geometry.Point(coordList.get(2))
    topLeft = ee.Geometry.Point(coordList.get(3))

    # if len(pntsList) > 0:
    pntsFilter = ee.Filter.And(
        # ee.Filter.geometry(btmLeft),
        ee.Filter.geometry(btmRight),
        # ee.Filter.geometry(topRight),
        ee.Filter.geometry(topLeft)
    )

    return pntsFilter

cfg = edict({
    "roi_cloud_level": 20, # cloud percentage range from 0 - 100, 0 for cloud-free
    "filter_by_cloud": True,
    # "S2_BANDS": ['B2', 'B3', 'B4', 'B8', 'B11', 'B12'],
    "S2_BANDS": ['B4', 'B8', 'B12'], # Red, NIR, SWIR2, cloud band
    # "S2_BANDS": ['NBR1'],
    "extend_months": 0, # 1
})

# Wildfire Event
EVENT_SET = edict({

    'CA2023XXXXX': {
        "name": "CA2023XXXXX",
        "roi": [-121.7697, 50.6512, -120.7068, 51.5224],
        "year": 2023,
        'crs': "EPSG:32610",

        "modisStartDate": "2023-06-01",
        "modisEndDate": "2023-12-31",

        "where": 'non-known'
    },

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

    'CA_2021_Kamloops': {
        "name": "US_2021_Kamloops",
        "roi": [-122.50374742390655,50.01650250726357,
                -120.22957750203155,51.70484697718656],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-06-25",
        "modisEndDate": "2021-09-10",

        'orbKeyList': ['DSC13'],

        "where": 'CA'
    },

    'US_2021_Dixie': {
        "name": "US_2021_Dixie_V3",
        "roi": [-121.75405666134564,39.5671341526342,
                -119.88638088009564,40.92552027566895],
        "year": 2021,
        'crs': "EPSG:32610",

        "modisStartDate": "2021-06-16",
        "modisEndDate": "2021-09-17",

        "where": 'US'
    },
    
    "CA_2023_Donnie": {
        "name": "CA_2023_Donnie_creek",
        "roi_raw": [[[-123.07241687918899,57.63762538884546],[-122.78743667308454,57.642392735216305],[-122.6676045217305,57.50024857293588],[-122.54507312918899,57.32460952766016],[-122.46518799736943,57.21322401912293],[-122.1111131682515,57.008904565450976],[-121.96852281914117,57.00723637916713],[-121.79636743341221,57.02126665206546],[-121.35854969168899,57.08659126475191],[-120.72151367056527,57.17998045521142],[-120.57852039481399,57.44895558350533],[-120.567534066689,57.77848752183324],[-120.73494056021961,57.94156122827197],[-121.20474109793898,57.91880231576013],[-121.49700982265956,57.922644284050335],[-121.72891318035441,58.151133218258835],[-121.89764546597104,58.15808111510419],[-122.05508252353346,58.08362860125648],[-122.23965969023266,58.063972249819834],[-122.88769479130461,57.8659056752724],[-123.07241687918899,57.63762538884546]]],
        "year": 2023,
        "crs": "EPSG:32610",
        
        "modisStartDate": "2023-08-25",
        "modisEndDate": "2023-08-27",
        
        "where": 'CA'
    },
    
       "CA_2023_Buffalo": {
        "name": "CA_2023_Buffalo_National_Park",
        "roi_raw": [[[-112.7547383781353,59.6299948883513],[-112.70306807368527,59.518815036700204],[-112.67552879642714,59.34199387028242],[-112.41553593832946,59.28251005521115],[-112.15027994437914,59.312228880556034],[-111.98847047713762,59.35332645451057],[-112.0241475578228,59.45596783454793],[-112.05778022234078,59.51670576325207],[-112.02354132254987,59.52489519925496],[-112.03119676208898,59.55280237855959],[-112.03859559290885,59.5821637438142],[-112.02412237203248,59.60310416266941],[-112.0065410292983,59.732069623580784],[-112.23014121016655,59.836263035105205],[-112.46068376278168,59.87096027468018],[-112.64212851485406,59.841782909007186],[-112.75758950981059,59.789080074023694],[-112.88262865971537,59.75993919612461],[-112.8920938586314,59.68094857390355],[-112.7547383781353,59.6299948883513]]],
        "year": 2023,
        "crs": "EPSG:32610",
        
        "modisStartDate": "2023-05-29",
        "modisEndDate": "2023-07-27",
        
        "where": 'CA'
    },
       
       "CA_2023_Slave": {
        "name": "CA_2023_Slave_Lake",
        "roi_raw": [[[-116.56841659311138,55.349513493590486],[-116.42712116958133,55.21607298240847],[-116.37959301716279,55.077807773337355],[-116.54601758978865,55.0275149923394],[-116.87560743353862,54.98368056482151],[-116.84814161322618,54.9133088398647],[-116.8461010518372,54.865829569425976],[-116.59107511768025,54.82766682901822],[-116.23499257584025,54.76002239507742],[-115.57784742377304,54.74561030806731],[-115.41854079869404,54.81249722066167],[-114.94476026556993,55.02803484564705],[-114.94201368353862,55.121338617696374],[-115.25237745306988,55.1555249286488],[-115.26611036322616,55.16355241008233],[-115.27654200660517,55.16776538931513],[-115.6149839493118,55.22613373847155],[-116.14503569189567,55.405912572708175],[-116.57073682806988,55.39040126669515],[-116.56841659311138,55.349513493590486]]],
        "year": 2023,
        "crs": "EPSG:32610",
        
        "modisStartDate": "2023-05-04",
        "modisEndDate": "2023-07-27",
        
        "where": 'CA'
    },
       "CA_2023_Trout": {
           "name": "CA_2023_Trout_Lake",
           "roi_raw": [[[-122.11151855468755,59.52264598865422],[-118.33222167968756,59.52264598865422],[-118.33222167968754,60.63497753709193],[-122.11151855468752,60.63497753709193],[-122.11151855468755,59.52264598865422]]],
           "year": 2023,
            "crs": "EPSG:32610",
            
            "modisStartDate": "2023-08-06",
            "modisEndDate": "2023-08-07",
            
            "where": 'CA'
       },
       
        "CA_2023_YellowKnife": {
           "name": "CA_2023_YellowKnife",
           "roi_raw": [[[-116.30928563104779,61.917461847406514],[-112.76070164667279,61.917461847406514],[-112.76070164667279,63.62598104484547],[-116.30928563104779,63.62598104484547],[-116.30928563104779,61.917461847406514]]],
           "year": 2023,
            "crs": "EPSG:32610",
            
            "modisStartDate": "2022-08-25",
            "modisEndDate": "2022-08-26",
            
            "where": 'CA'
       },
       "CA_2023_Kelowna": {
           "name": "CA_2023_Kelowna",
        #    "roi_raw": [[[-119.8524532463199,49.76241111347969],[-119.32236291428865,49.76241111347969],[-119.32236291428865,50.108023140332],[-119.8524532463199,50.108023140332],[-119.8524532463199,49.76241111347969]]],
            "roi_raw": [[[-119.63409997483554,49.87228541683829],[-119.3251094963199,49.87228541683829],[-119.3251094963199,50.08776161803331],[-119.63409997483554,50.08776161803331],[-119.63409997483554,49.87228541683829]]],
           "year": 2023,
            "crs": "EPSG:32610",
            
            "modisStartDate": "2023-08-15",
            "modisEndDate": "2023-08-16",
            
            "where": 'CA'
       },
    
    

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


# event = EVENT_SET['CA2017Elephant']

for name in ['CA_2023_Donnie']: # list(EVENT_SET.keys())[:1]:
    event = EVENT_SET[name]

    event['start_date'] = event['modisStartDate']
    event['end_date'] = event['modisEndDate']
    event['year'] = ee.Number(event['year']).format().getInfo()
    event['roi'] = ee.Geometry.Polygon(event['roi_raw']).bounds().getInfo()['coordinates'][0]
    print(event['roi'])
    # getting only the coordinates required for the ee.geometry.Rectangle method
    event['roi'] = [event['roi'][0], event['roi'][2]]
    
    
    event['pntsFilter'] = get_pntsFilter(ee.Geometry.Rectangle(event['roi']), -1000)

    event['roi'] = ee.Geometry.Rectangle(event['roi']).getInfo()['coordinates'][0]
    
    

    

    pprint(event['roi'])
    # exit(0)
    # Query Progression and Export 
    from gee.progression import query_progression_and_export
    print(f"-----------------> {event.name} <------------------ ")

    query_progression_and_export(
        cfg, 
        event, 
        scale=20, # spatial resolution
        BUCKET="wildfire-prg-dataset-v1", # GCP
        export_sat=['S2'],
        get_pre = False,
        # export_sat=['S1', 'S2', 'mask', 'AUZ']
    )