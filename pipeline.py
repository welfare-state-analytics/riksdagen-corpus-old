from parliament_data.download import login_to_archive
from parliament_data.segmentation import instance_workflow, infer_metadata, gen_parlaclarin_corpus
import pandas as pd
import os
from parliament_data.curation import curation_workflow, get_curated_blocks

def curations(file_db, archive, pattern_db):
    file_db_years = sorted(list(set(file_db["year"])))
    print("Years to be iterated", file_db_years)
    instance_dbs = []
    for corpus_year in file_db_years:
        
        year_db = file_db[file_db["year"] == corpus_year]
        #year_db = year_db.head(3)
        package_ids = year_db["package_id"]
        package_ids = list(package_ids)
        package_ids = sorted(package_ids)

        year_folder = "db/curation/instances/"+ str(corpus_year) + "/"
        if not os.path.exists(year_folder):
            os.makedirs(year_folder)
        
        for package_id in package_ids:
            instance_db = curation_workflow(package_id, archive, pattern_db)
            instance_db.to_csv(year_folder + package_id + ".csv")
            instance_dbs.append(instance_db)
    
    instance_db = pd.concat(instance_dbs)
    print(instance_db)

    return instance_db

def instances(file_db, archive, pattern_db, mp_db):
    file_db_years = sorted(list(set(file_db["year"])))
    print("Years to be iterated", file_db_years)
    instance_dbs = []
    for corpus_year in file_db_years:
    
        year_db = file_db[file_db["year"] == corpus_year]
        package_ids = year_db["package_id"]
        package_ids = list(package_ids)
        package_ids = sorted(package_ids)

        year_folder = "db/segmentation/instances/"+ str(corpus_year) + "/"
        if not os.path.exists(year_folder):
            os.makedirs(year_folder)
        
        for package_id in package_ids:
            metadata = infer_metadata(package_id)
            instance_db = instance_workflow(package_id, archive, pattern_db, mp_db)
            instance_db.to_csv(year_folder + package_id + ".csv")
            instance_dbs.append(instance_db)
    
    instance_db = pd.concat(instance_dbs)
    print(instance_db)

    return instance_db

def parlaclarin(file_db, archive, instance_db=None):
    file_db_years = sorted(list(set(file_db["year"])))
    #file_db_chambers = sorted(list(set(file_db["chamber"])))
    print("Years to be iterated", file_db_years)
    for corpus_year in file_db_years:
    
        year_db = file_db[file_db["year"] == corpus_year]
        year_db = year_db
        package_ids = year_db["package_id"]
        package_ids = list(package_ids)
        package_ids = sorted(package_ids)
        
        all_current_instances = []
        
        all_current_curations = []
        for package_id in package_ids:
            if instance_db is None:
                year_folder = "db/segmentation/instances/"+ str(corpus_year) + "/"
                current_instances = pd.read_csv(year_folder + package_id + ".csv")
            else:
                current_instances = instance_db[instance_db["filename"] == package_id]
            all_current_instances.append(current_instances)
            year_folder = "db/curation/instances/"+ str(corpus_year) + "/"
            
            current_curations = pd.read_csv(year_folder + package_id + ".csv")
            all_current_curations.append(current_curations)
            
        
        current_instances = pd.concat(all_current_instances)
        current_curations = pd.concat(all_current_curations)
        print(current_instances)
        print(current_curations)
        
        corpus_metadata = dict(
            document_title="Riksdagens protocols " + str(corpus_year),
            authority="National Library of Sweden and the WESTAC project",
            correction="Some data curation was done. It is documented in db/curation/instances"
        )
        parla_clarin_str = gen_parlaclarin_corpus(year_db, archive, current_instances, corpus_metadata=corpus_metadata, curation_instance_db=current_curations)
        
        parlaclarin_path = "data/parla-clarin/" + "corpus" + str(corpus_year) + ".xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()

if __name__ == "__main__":
    
    file_db = pd.read_csv("db/protocols/files.csv")
    
    start_year = 1951
    end_year = 1975
    
    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    
    mp_db = pd.read_csv("db/mp/1921-2022.csv")
    pattern_db = pd.read_json("db/segmentation/patterns.json", orient="records", lines=True)
    archive = login_to_archive()
    
    if False:
        curation_pattern_db = pd.read_json("db/curation/patterns.json", orient="records", lines=True)
        curation_instance_db = curations(file_db, archive, curation_pattern_db)
    else:
        curation_instance_db = None
        
    if False:
        instance_db = instances(file_db, archive, pattern_db, mp_db)
    else:
        instance_db = None
    
    if True:
        parlaclarin(file_db, archive, instance_db = instance_db)



