
import json
import ee

keyfile='private_keys/nrt-wildfiremonitoring.json'
key=json.load(open(keyfile))
service_account=key['client_email']
credentials = ee.ServiceAccountCredentials(service_account, keyfile)
ee.Initialize(credentials)

queryEvent = {
    'start_date': '2023-05-04',
    'end_date': '2023-05-05',
    'year': 2023,
    'roi': ee.Geometry.Rectangle([-123.134, 57.023, -120.344, 58.171])
}

from gee.export import update_query_event, query_s1s2_and_export
query_s1s2_and_export(queryEvent, 
            scale=100, 
            BUCKET="wildfire-prg-dataset-100m",
            dataset_folder="CA_2023_Donnie_Creek",
            export=['S1']
        )