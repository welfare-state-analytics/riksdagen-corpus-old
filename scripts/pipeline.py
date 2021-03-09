import pandas as pd
import progressbar
from pyriksdagen.download import LazyArchive
from pyriksdagen.segmentation import segmentation_workflow
from pyriksdagen.curation import curation_workflow
from pyriksdagen.export import parlaclarin_workflow
from pyriksdagen.export import parlaclarin_workflow_individual
from pyriksdagen.db import load_db, save_db, load_patterns

def main():    
    file_dbs = []
    file_dbs.append(pd.read_csv("input/protocols/scanned.csv"))
    file_dbs.append(pd.read_csv("input/protocols/digital_originals.csv"))
    file_db = pd.concat(file_dbs)
    
    start_year = 1920
    end_year = 2021

    start_year = 1955
    end_year = 1955
    
    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    
    mp_db = pd.read_csv("corpus/members_of_parliament.csv")
    archive = LazyArchive()
    
    if False:
        curation_patterns = load_patterns(phase="curation")
        curation_db = curation_workflow(file_db, archive, curation_patterns)
        save_db(curation_db, phase="curation")
    else:
        print("Load curation database...")
        curation_db = load_db(phase="curation")
        print("Done.")
        
    if True:
        segmentation_patterns = load_patterns(phase="segmentation")
        segmentation_db = segmentation_workflow(file_db, archive, segmentation_patterns, mp_db, ml=False)
        save_db(segmentation_db, phase="segmentation")
    else:
        print("Load segmentation database...")
        segmentation_db = load_db(phase="segmentation")
        print("Done.")
    
    if True:
        parlaclarin_workflow_individual(file_db, archive, curations=curation_db, segmentations=segmentation_db)


if __name__ == "__main__":
    main()