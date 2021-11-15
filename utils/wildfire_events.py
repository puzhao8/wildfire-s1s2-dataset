import ee

"""////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////"""
""" ================================================================= Study Areas ==================================================================== """
"""////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////"""

Reka_Yana = {
    'name': 'Reka_Yana',
    'roi': ee.Geometry.Rectangle([133.63988741949532,69.28583594825527, 
                                  134.67809542730777,69.65568955613385]),
    'crs': 'EPSG:32653',

    'startDate': '2019-05-01',  # 2019-05-18
    'endDate': '2019-08-15',  # 2019-10-01

    # MSI
    'S2_Master': '2019-12-03',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.02,

    # SAR
    # 'ASC20': '2019-05-14',

    # SAR-orbit
    # 'orbNumList': [137, 144],
    'bandList': ['VV', 'VH']
}


Lena_River = {
    'name': 'Lena_River',
    'roi': ee.Geometry.Rectangle([123.96093234137032,66.13000572929009, 
                                  125.87804659918278,66.71878253253996]),
    'crs': 'EPSG:32653',

    'startDate': '2019-07-01',  # 2019-05-18
    'endDate': '2019-12-20',  # 2019-10-01

    # MSI
    'S2_Master': '2019-07-12',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.02,

    # SAR
    # 'ASC20': '2019-05-14',

    # SAR-orbit
    # 'orbNumList': [137, 144],
    'bandList': ['VV', 'VH']
}

"""--------------------------------------------------------------------------------"""
Thomas_roi = ee.Geometry.Rectangle([-119.7345, 34.2277, -118.8913, 34.6524])
Thomas = {
    'name': 'Thomas',
    'roi': Thomas_roi,
    'crs': 'EPSG:32611',

    'startDate': '2017-12-04',  # 2019-05-18
    'endDate': '2017-12-31',  # 2019-10-01

    # MSI
    'S2_Master': '2017-12-03',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.02,

    # SAR
    # 'ASC20': '2019-05-14',

    # SAR-orbit
    'orbNumList': [137, 144],
    'bandList': ['VV', 'VH']
}


''' ------------------------- Mendocino Complex Fires (2018) ---------------------------'''
Mendocino_roi = ee.Geometry.Polygon(
        [[[-123.24357584228193, 39.584004430927514],
            [-123.24357584228193, 38.918294081354006],
            [-122.35917642821943, 38.918294081354006],
            [-122.35917642821943, 39.584004430927514]]])

Mendocino_Fire = {
    'name': 'Mendocino',
    'roi': Mendocino_roi,
    # 'crs': 'EPSG:32611',

    'startDate': '2018-07-27',  # 2019-05-18
    'endDate': '2018-10-01',  # 2019-10-01

    # MSI
    'S2_Master': '2018-07-27',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.2,

    # SAR-orbit
    # 'orbNumList': [137, 144],
    'bandList': ['VV', 'VH']
}


''' ------------------------- Sweden Fires (2018) ---------------------------'''
OrrmoSE = (
    ee.Geometry.Polygon(
        [[[13.894223411877253, 61.93915882230737],
            [13.894223411877253, 61.87804999977173],
            [14.026745994885065, 61.87804999977173],
            [14.026745994885065, 61.93915882230737]]]))


OrrmoSE_fire = {
    'name': 'OrrmoSE',
    'roi': OrrmoSE,

    'startDate': '2018-07-01',  # 2019-05-18
    'endDate': '2018-10-01',  # 2019-10-01

    # MSI
    'S2_Master': '2018-07-04',  # good S2 prefire date

    # SAR
    'DSC168': '2018-07-04',
    'ASC175': '2018-06-28',  # prefire date
    'ASC73': '2018-06-21',
    # 'ASC20': '2017-05-12',
    # SAR-orbit

    'bandList': ['VV', 'VH']
}


'''--------------------------- Swedish Fires --------------------------------'''
### Karbole Wildfire 2018, Sweden
Ljusdals_roi = ee.Geometry.Rectangle([
    15.137434283688016, 61.86566784664094,
    15.604353229000516, 62.06961520427164])

Ljusdals_SE = { # Karbole_SE
    'name': 'SE2018Ljusdals', # Enskogen (A, C, F), 
    'roi': Ljusdals_roi,
    'crs': 'EPSG:32633',

    'startDate': '2018-07-15',  # 2019-05-18
    'endDate': '2018-08-10',  # 2019-10-01
    # 'msiExportDates': ['2018-07-16', '2018-07-17','2018-07-19', '2018-07-24','2018-07-26',
    #                     '2018-07-27','2018-07-31','2018-08-03','2018-08-08'],

    # MSI Master Dates
    'S2_Master': '2018-07-04',  # good S2 prefire date
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR Master Dates
    # 'ASC102': '',
    'DSC66': '2018-07-09',
    'DSC168': '2018-07-10',
    'DSC95': '2018-07-11',  # '2018-07-05',

    # SAR-orbit
    # 'orbNumList': [66, 168, 95], 
    'bandList': ['VV', 'VH']
}

'''--------------- Trangslet_SE -----------------------'''
Trangslet_roi = ee.Geometry.Rectangle(
    [ 13.458252, 61.562612,
      13.669739,  61.656313])

Trangslet_SE = { # Trängslet (D)
    'name': 'SE2018Trangslet',
    'roi': Trangslet_roi,
    'crs': 'EPSG:32633',

    'startDate': '2018-07-14',  # 2019-05-18
    'endDate': '2018-08-10',  # 2019-10-01

    # MSI
    'S2_Master': '2017-11-06',  # good S2 prefire date
    'L8_Master': '2017-07-05',  # good L8 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,

    'bandList': ['VV', 'VH']
}


'''--------------- Fajelsjo_SE -----------------------'''
Lillasen_roi = ee.Geometry.Rectangle(
    [14.294493268239412,61.74791901310678,
        14.581511090505037,61.87830201446005])

Lillasen_SE = {
    'name': 'SE2018Lillasen', #  Lillåsen (B)
    'roi': Lillasen_roi,
    'crs': 'EPSG:32633',

    'startDate': '2018-07-15',  # 2019-05-18
    'endDate': '2018-08-10',  # 2019-10-01

    # MSI
    'S2_Master': '2017-11-06',  # good S2 prefire date
    'L8_Master': '2017-07-05',  # good L8 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,

    # SAR
    'DSC168': '2018-07-04',
    'ASC175': '2018-06-28',  # prefire date
    'ASC73': '2018-06-21',
    # 'ASC20': '2017-05-12',
    # SAR-orbit
    # 'orbNumList': [66, 73, 168],
    'bandList': ['VV', 'VH']
}


'''-----------------------------------------------------------'''
Storbrattan_roi = ee.Geometry.Rectangle(
    [13.889465, 61.883019,  
     14.021301, 61.941534])

Storbrattan_SE = {
    'name': 'SE2018Storbrattan', # 'E'
    'roi': Storbrattan_roi,
    'crs': 'EPSG:32633',

    'startDate': '2018-07-15',  # 2019-05-18
    'endDate': '2018-08-10',  # 2019-10-01

    # MSI
    'S2_Master': '2017-11-06',  # good S2 prefire date
    'L8_Master': '2017-07-05',  # good L8 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.1,

    # SAR
    # 'DSC168': '2018-07-04',
    # 'ASC175': '2018-06-28',  # prefire date
    # 'ASC73': '2018-06-21',
    # 'ASC20': '2017-05-12',
    # SAR-orbit
    # 'orbNumList': [66, 73, 168],
    'bandList': ['VV', 'VH']
}


""" ==============================> Chuckegg Wildfire (2019) <==============================="""
CA_Chuckegg_roi = (ee.Geometry.Rectangle(
    [-118.15516161677635, 58.80344955293542,
        -116.58411669490135, 57.78735191577551]))
Chuckegg = {
    'name': 'Chuckegg',
    'roi': CA_Chuckegg_roi,
    'crs': 'EPSG:32611',

    'startDate': '2019-05-18',  # 2019-05-18
    'endDate': '2019-08-20',  # 2019-10-01

    'msiExportDates': ['2019-05-21', '2019-05-24', '2019-05-26', '2019-05-28', 
                        '2019-06-10', '2019-06-17', '2019-06-25', '2019-07-11', '2019-07-15', 
                        '2019-07-17', '2019-07-20', '2019-08-06', '2019-08-12'],

    # MSI
    'S2_Master': '2019-05-16',  # good S2 prefire date
    'L8_Master': '2019-07-05',  # good L8 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.02,

    # SAR
    'ASC20': '2019-05-14',
    # SAR-orbit
    'orbNumList': [20],
    'bandList': ['VV', 'VH']
}

""" ============================= Elephant Wildfire (2017) =============================== """
elephant_roi = ee.Geometry.Rectangle([-121.7697, 50.6512, -120.7068, 51.5224])

    #   - -121.57561199349276
    #   - 50.70320856227638
    #   - -120.88920659710276
    #   - 51.50342946634545

elephant_refPoly = ee.FeatureCollection("users/omegazhangpzh/elephant_refPoly")

elephantFire = {
    'name': 'elephant',
    'roi': elephant_roi,
    'poly': elephant_refPoly,
    'crs': 'EPSG:32610',
    'groupLevel': 10,

    'startDate': '2017-07-07',  # 2017-07-07
    'endDate': '2017-09-29',  # 2017-10-01

    # MSI
    'S2_Master': '2017-11-06',  # good S2 prefire date
    'L8_Master': '2017-07-05',  # good L8 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,

    # SAR
    'DSC13': '2017-05-17',
    'DSC115': '2017-05-12',  # prefire date
    'ASC64': '2017-06-26',

    # SAR-orbit
    'orbNumList': [64], # 64, 13, 115, 
    'bandList': ['VV', 'VH']
}

""" ============================= Sydney Wildfire (2019) ======================================= """
Sydney_roi = (ee.Geometry.Rectangle(
    [149.62892366273888, -34.46629366617598,
        151.60646272523888, -32.24350555003469]))

Sydeny_InSAR_quaryROI = (ee.Geometry.Rectangle(
    [149.63166990949395,-34.005666372616766,
        151.34553709699395,-32.304208548926596]))

Sydney_msiExportDateList = ['2019-10-22',  # master
        '2019-10-27', '2019-10-28', '2019-11-01', '2019-11-06', '2019-11-11', '2019-11-13', '2019-11-21',
        '2019-12-16', '2019-12-21', '2019-12-26', '2019-12-31', '2020-01-05', '2020-01-10',
        '2019-12-11',  # a bit cloudy, but still good to use
        # '2019-12-15', # not good
        ]

Sydney_sarExportDateList = ['2019-10-16', '2019-10-25', '2019-10-28', '2019-11-06', '2019-11-09', '2019-11-18', '2019-11-21', '2019-11-27',
                        '2019-11-30', '2019-12-12', '2019-12-15', '2019-12-24', '2019-12-27', '2020-01-05',
                        '2020-01-08']

Sydney_AU = {
    'name': 'Sydney',
    'roi': Sydney_roi,  # Sydney_roi_1111,
    'poly': Sydney_roi,
    'crs': 'EPSG:4326',  # 'EPSG:3577', # EPSG:3577
    'pntsRect': (ee.Geometry.Rectangle([150.0941018581052, -34.12241279581038,
                                        151.1927346706052, -32.894960055302946])),  # AU

    'startDate': '2019-10-27',  # 2019-10-22
    'endDate': '2020-01-11',  # 2018-12-10
    'msiExportDates': Sydney_msiExportDateList,
    'sarExportDates': Sydney_sarExportDateList,

    'S2_Master': '2019-10-22',
    'CGLC_2015': 112,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2018-11-06',

    'ASC9': '2019-10-16',
    'DSC147': '2019-10-25',  # prefire date
    # 'DSC42': '2018-11-04',
    # 'ASC137': '2018-11-05',
    #
    # 'orbitList': ['ASC35', 'DSC115', 'DSC42', 'ASC137'],
    'orbNumList': [9, 147], # 147
    'bandList': ['VV', 'VH']
}


FraserIsland = {
    'name': 'FraserIsland',
    'roi': ee.Geometry.Rectangle([ # Fraser Island's bushfire, AU
        -207.034607, -25.495347,
        -206.603394, -24.666986]),

    'startDate': '2020-10-14',
    'endDate': '2020-12-25',
 
    'S2_Master': '2020-09-26',
}


### Chernobyl Fire
Chernobyl_roi = ee.Geometry.Rectangle([
    28.99813777465401,51.11025426596282,
    29.867430987544633,51.47437610351912,
    # 29.620238604732133,51.36132691631253
    ])

Chernobyl_Ukrayina = {
    'name': 'Chernobyl',
    'roi': Chernobyl_roi,
    'crs': 'EPSG:32635',

    'startDate': '2020-03-26',  # 2020-04-04
    'endDate': '2020-07-01',  # 2019-10-01
    'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-03-26',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR Master Dates
    'DSC36': '2020-03-28',
    'ASC160': '2020-03-30', 
    'ASC87': '2020-03-31',
    'DSC109': '2020-04-02',
    
    # SAR-orbit
    # 'orbNumList': [66, 168, 95], 
    'bandList': ['VV', 'VH']
}

# anyFire
Bighorn_roi = ee.Geometry.Rectangle([
    -110.98381034548756,32.27360607200184,
    -110.53337089236256,32.621274592521054,
    ])# S2_master: 2020-05-29

Mangum_roi = ee.Geometry.Rectangle([
    -112.40653983767506,36.58063203834924,
    -112.06596366580006,36.959054670725436,
    ])# S2_master: 2020-06-06


Mangum_2020 = {
    'name': 'Mangum',
    'roi': Mangum_roi,
    # 'crs': 'EPSG:32610',

    'startDate': '2020-06-01',  # 2020-04-04
    'endDate': '2020-07-01',  # 2019-10-01
    # 'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-06-01',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # Tucson_Bighorn2020
    'orbNumList': [27, 20], 
    'ASC20': '2020-06-07',
    'DSC27': '2020-06-01',

    # SAR-orbit 
    'bandList': ['VV', 'VH']
}

azBush_roi = ee.Geometry.Rectangle([
    -111.64660565026134,33.52572899836681,
    -111.11926190026134,34.05984422061784,
    ])# S2_master: 2020-06-08
azBushFire_2020 = {
    'name': 'AZ_Bush',
    'roi': azBush_roi,
    # 'crs': 'EPSG:32610',

    'startDate': '2020-06-14',  # 2020-04-04
    'endDate': '2020-10-01',  # 2019-10-01
    # 'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-06-08',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # Tucson_Bighorn2020
    'orbNumList': [27, 20], 
    'ASC20': '2020-06-07',
    'DSC27': '2020-06-01',

    # SAR-orbit 
    'bandList': ['VV', 'VH']
}

Bighorn_2020 = {
    'name': 'Tucson',
    'roi': Bighorn_roi,
    # 'crs': 'EPSG:32610',

    'startDate': '2020-05-09',  # 2020-04-04
    'endDate': '2020-07-01',  # 2019-10-01
    # 'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-05-29',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR Master Dates
    # 'DSC36': '2020-03-28',
    # 'ASC160': '2020-03-30',
    #
    # Tucson_Bighorn2020
    'orbNumList': [27, 129], 
    'DSC27': '2020-06-01',
    'DSC129': '2020-06-08',
    
    
    # SAR-orbit 
    'bandList': ['VV', 'VH']
}

Arctic_roi = ee.Geometry.Rectangle([
    144.33563197786555,71.08969831476905,
    145.98358119661555,71.55062468956767,
    ])# S2_master: 'EPSG:32654'

Arctic_large_roi = ee.Geometry.Rectangle([
    148.20518948464075,66.32115392343614,
    155.28038479714075,69.55100165197304,
    ])# S2_master: 'EPSG:32655-32656'

Arctic_KolymaRiver_2020 = ee.Geometry.Rectangle([
    153.4267781118101,67.03794232033776,
    154.9923298696226,67.624344440998,
    ]) # S2_master: 'EPSG:32656'

KolymaRiverFire = {
    'name': 'Arctic_KolymaRiver',
    'roi': Arctic_KolymaRiver_2020,
    'crs': 'EPSG:32656',

    'startDate': '2020-06-18',  # 2020-04-04
    'endDate': '2020-09-13',  # 2019-10-01
    # 'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-06-18',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # Tucson_Bighorn2020
    # 'orbNumList': [27, 129], 

    # SAR Master Dates
    'DSC27': '2020-06-01',
    'DSC129': '2020-06-08',
            
    # SAR-orbit 
    'bandList': ['VV', 'VH']
}

Arctic_Large_2020 = {
    'name': 'ArcticLarge',
    'roi': Arctic_large_roi,
    'crs': 'EPSG:32656',

    'startDate': '2020-06-14',  # 2020-04-04
    'endDate': '2020-08-01',  # 2019-10-01
    # 'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-05-29',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # Tucson_Bighorn2020
    # 'orbNumList': [148],

    # SAR Master Dates
    'DSC27': '2020-06-01',
    'DSC148': '2020-06-15',
            
    # SAR-orbit 
    'bandList': ['VV', 'VH']
}

'''---------------------- California Wildfire 2020 ---------------------------'''
CAL_SCU_roi = ee.Geometry.Rectangle([
    -121.829577917969,37.08876178359257,
    -121.09079155538969,37.644787113374456,
    ])# S2_master: 2020-06-08

CAL_LNU_roi = ee.Geometry.Rectangle([
    -122.64976069609375,38.35467732219108,
    -121.7681078640625,39.023547487051566,
    ])# S2_master: 2020-06-08
CAL_SCU_2020 = {
    'name': 'CAL_SCU',
    'roi': CAL_SCU_roi,
    'crs': 'EPSG:32610',

    'startDate': '2020-08-17',  # 2020-04-04
    'endDate': '2020-10-01',  # 2019-10-01
    # 'msiExportDates': ['2020-04-05', '2020-04-10', '2020-04-17', '2020-06-21'],

    # MSI Master Dates
    'S2_Master': '2020-08-12',  # good S2 prefire date
    'CGLC_2015': 111,
    'dNBR1_TH': 0.05,

    # SAR-orbit 
    # 'orbNumList': [148],
    'bandList': ['VV', 'VH']
}


### Karbole Wildfire 2018, Sweden
DoctorCreek_roi = ee.Geometry.Rectangle([
    -116.29013161295042,49.98329765861565,
    -115.77377419107542,50.30014276736378])

DoctorCreek_roi_small = ee.Geometry.Rectangle([
    -116.22883394897953,49.987938830485305,
    -115.93357638062015,50.169483949045514]);   

DoctorCreekFire = {
    'name': 'DoctorCreek_small',
    'roi': DoctorCreek_roi_small,
    'crs': 'EPSG:32611',

    'startDate': '2020-08-18',  # 2019-05-18
    'endDate': '2020-09-30',  # 2019-10-01
    # 'msiExportDates': ['2018-07-16', '2018-07-17','2018-07-19', '2018-07-24','2018-07-26',
    #                   '2018-07-27','2018-07-31','2018-08-03','2018-08-08'],

    # MSI Master Dates
    'S2_Master': '2020-08-04',  # good S2 prefire date, or '2020-08-04'
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR-orbit
    # 'orbNumList': [66, 168, 95], 
    'bandList': ['VV', 'VH']
}


### Karbole Wildfire 2018, Sweden
AugustComplex_roi_large = ee.Geometry.Rectangle([
    -123.74777724951768,39.204783258127826,
    -122.17123916358018,40.33626642155187])

AugustComplex_roi = ee.Geometry.Rectangle([
    -123.57474258154893,39.391824170134846,
    -122.48434951514268,40.23360174430179])

AugustComplexFire = {
    'name': 'AugustComplex',
    'roi': AugustComplex_roi,
    'crs': 'EPSG:32610',

    'startDate': '2020-08-15',  # 2019-05-18
    'endDate': '2020-10-30',  # 2019-10-01
    # 'msiExportDates': ['2018-07-16', '2018-07-17','2018-07-19', '2018-07-24','2018-07-26',
    #                   '2018-07-27','2018-07-31','2018-08-03','2018-08-08'],

    # MSI Master Dates
    'S2_Master': '2020-08-15',  # good S2 prefire date
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR-orbit
    'orbNumList': [35, 115], 
    'bandList': ['VV', 'VH']
}

Beechie_roi = ee.Geometry.Rectangle([
    -122.69308974951768,44.54759737613707,
    -121.50381972998643,45.35038981526233])

BeechieFire = {
    'name': 'Beechie',
    'roi': Beechie_roi,
    'crs': 'EPSG:32610',

    'startDate': '2020-08-15',  # started 2020-08-16T11:18AM
    'endDate': '2020-10-30',  # 2019-10-01
    # 'msiExportDates': ['2018-07-16', '2018-07-17','2018-07-19', '2018-07-24','2018-07-26',
    #                   '2018-07-27','2018-07-31','2018-08-03','2018-08-08'],

    # MSI Master Dates
    'S2_Master': '2020-08-15',  # good S2 prefire date
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR-orbit
    'orbNumList': [137, 115, 13], 
    'bandList': ['VV', 'VH']
}

CAL_Creek_roi = ee.Geometry.Rectangle([
    -119.74051406592393,36.932528832375546,
    -118.90005996436143,37.690537720495435])

CAL_CreekFire = {
    'name': 'CAL_Creek',
    'roi': CAL_Creek_roi,
    'crs': 'EPSG:32611',
    'groupLevel': 13,

    'startDate': '2020-09-03',  # 2019-05-18
    'endDate': '2020-10-30',  # 2019-10-01
    # 'msiExportDates': ['2018-07-16', '2018-07-17','2018-07-19', '2018-07-24','2018-07-26',
    #                   '2018-07-27','2018-07-31','2018-08-03','2018-08-08'],

    # MSI Master Dates
    'S2_Master': '2020-09-03',  # good S2 prefire date
    # 'L8_Master': '2017-07-05',  # good L8 prefire date

    # SAR-orbit
    'orbNumList': [144, 64, 137], 
    'bandList': ['VV', 'VH']
}


""" ================ added on Nov 7, 2020 ======================= """
# 'name': 'Siberia_Zhigansk',
# 'roi': ee.Geometry.Rectangle([
#         123.96093234137032,66.13000572929009,
#         125.87804659918278,66.71878253253996]),

# 'name': 'Siberia_Morkoka',
# 'roi': ee.Geometry.Rectangle([ # Sebirian fire 1
#         112.74557309452663,63.982359204277664,
#         114.29464536015163,64.6583554409014]),

# 'name': 'AU_Nowra',

    
AU_Nowra = {
    'name': 'AU_Nowra',
    'roi': ee.Geometry.Rectangle([
        149.9078601138805,-35.37837920839537,
        150.65218384434925,-34.74439913086708]),
    'crs': 'EPSG:4326',

    'startDate': '2019-12-10',  # 2019-05-18
    'endDate': '2020-01-10',  # 2019-10-01
}

BZ_Conchas_2019 = {
    'name': 'BZ_Conchas_2019',
    'roi': ee.Geometry.Rectangle([ 
            -60.01524588889066,-17.561310201111475,
            -60.01524588889066,-17.561310201111475]),
    'crs': 'EPSG:4326',

    'startDate': '2019-12-10',  # 2019-05-18
    'endDate': '2020-01-10',  # 2019-10-01
}