import json
# Imports the Google Cloud client library
from google.cloud import storage

# gcloud config set project "ee-globalchange-gee4geo"
def save_json_to_bucket(project_id="ee-globalchange-gee4geo", 
                        bucket_name="eo4wildfire", 
                        json_file={}, 
                        json_url="first_text.json") -> None:

    # Instantiates a client
    storage_client = storage.Client()

    # The name for the new bucket
    # bucket_name = "eo4wildfire"

    # Creates the new bucket
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(json_url)

    blob.upload_from_string(
        data=json.dumps(json_file, ensure_ascii=False, indent=4),
        # content_type='application/json'
    )

def read_json_from_bucket(project_id="ee-globalchange-gee4geo", 
                            bucket_name="eo4wildfire", 
                            json_url="first_text.json") -> dict:
    ## Read json
    from prettyprinter import pprint

    storage_client = storage.Client(project=project_id)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(json_url)
    json_data = json.loads(blob.download_as_string())

    pprint(json_data)
    return json_data


if __name__ == "__main__":

    json_file = {
        'CLOUD': 'Google Cloud Platform'
    }

    json_url = "Wildfire_Benchmark_Dataset/fireEvent.json" # in gs://{bucket_name}
    save_json_to_bucket(
        project_id="ee-globalchange-gee4geo", 
            bucket_name="eo4wildfire", 
            json_file=json_file, 
            json_url=json_url)

    
    json_data = read_json_from_bucket(
        project_id="ee-globalchange-gee4geo", 
            bucket_name="eo4wildfire", 
            json_url=json_url)


    

