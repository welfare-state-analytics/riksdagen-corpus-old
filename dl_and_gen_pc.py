from parliament_data.download import login_to_archive
from parliament_data.segmentation import instance_workflow, infer_metadata, download_and_convert_to_parlaclarin
import pandas as pd


def instances(package_ids, archive, pattern_db, mp_db):
    instance_dbs = []
    for package_id in package_ids:
        metadata = infer_metadata(package_id)
        instance_db = instance_workflow(package_id, archive, pattern_db, mp_db)
        instance_db.to_csv("db/segmentation/instances/" + package_id + ".csv")
        instance_dbs.append(instance_db)
    
    instance_db = pd.concat(instance_dbs)
    print(instance_db)

    return instance_db

def parlaclarin(package_ids, archive, instance_db=None):
    for package_id in package_ids:
        if instance_db is None:
            current_instances = pd.read_csv("db/segmentation/instances/" + package_id + ".csv")
        else:
            current_instances = instance_db[instance_db["filename"] == package_id]

        parla_clarin_str = download_and_convert_to_parlaclarin(package_id, archive, current_instances, str_output=True)
        
        parlaclarin_path = "data/parla-clarin/" + package_id + ".xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()
        
    return parla_clarin_str

if __name__ == "__main__":
    
    file_db = pd.read_csv("db/protocols/files.csv")
    
    start_year = 1921
    end_year = 1950
    
    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    
    package_ids = file_db["package_id"]
    package_ids = list(package_ids)
    package_ids = sorted(package_ids)
    
    mp_db = pd.read_csv("db/mp/1921-2022.csv")
    pattern_db = pd.read_json("db/segmentation/patterns.json", orient="records", lines=True)
    archive = login_to_archive()
    
    if True:
        instance_db = instances(package_ids, archive, pattern_db, mp_db)
    else:
        instance_db = None
    
    parlaclarin(package_ids, archive, instance_db = instance_db)
    
    
    
    
