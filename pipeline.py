from parliament_data.download import login_to_archive
from parliament_data.segmentation import instance_workflow, infer_metadata, gen_parlaclarin_corpus
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

def parlaclarin(file_db, archive, instance_db=None):
    file_db_years = [1951]
    for corpus_year in file_db_years:
    
        year_db = file_db[file_db["year"] == corpus_year]
        package_ids = file_db["package_id"]
        package_ids = list(package_ids)
        package_ids = sorted(package_ids)[:3]
        
        all_current_instances = []
        for package_id in package_ids:
            if instance_db is None:
                current_instances = pd.read_csv("db/segmentation/instances/" + package_id + ".csv")
            else:
                current_instances = instance_db[instance_db["filename"] == package_id]
            all_current_instances.append(current_instances)
        
        current_instances = pd.concat(all_current_instances)
        
        corpus_metadata = dict(
            document_title="Riksdagens protocols " + str(corpus_year)
        )
        parla_clarin_str = gen_parlaclarin_corpus(package_ids, archive, current_instances, corpus_metadata=corpus_metadata)
        
        parlaclarin_path = "data/parla-clarin/" + "corpus" + str(corpus_year) + ".xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()

if __name__ == "__main__":
    
    file_db = pd.read_csv("db/protocols/files.csv")
    
    start_year = 1951
    end_year = 1951
    
    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    
    package_ids = file_db["package_id"]
    package_ids = list(package_ids)
    package_ids = sorted(package_ids)
    
    mp_db = pd.read_csv("db/mp/1921-2022.csv")
    pattern_db = pd.read_json("db/segmentation/patterns.json", orient="records", lines=True)
    archive = login_to_archive()
    
    if False:
        instance_db = instances(package_ids, archive, pattern_db, mp_db)
    else:
        instance_db = None
    
    parlaclarin(file_db, archive, instance_db = instance_db)



