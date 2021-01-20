import pandas as pd
import os
import progressbar

from riksdagen_corpus.download import login_to_archive
from riksdagen_corpus.segmentation import find_instances
from riksdagen_corpus.curation import curation_workflow
from riksdagen_corpus.export import gen_parlaclarin_corpus
from riksdagen_corpus.utils import infer_metadata
from riksdagen_corpus.db import load_db, save_db, load_patterns, year_iterator


def curations(file_db, archive, pattern_db):
    instance_dbs = []
    for corpus_year, package_ids, _ in year_iterator(file_db):
        print("Curating year:", corpus_year)
        
        for protocol_id in progressbar.progressbar(package_ids):
            instance_db = curation_workflow(protocol_id, archive, pattern_db)
            instance_dbs.append(instance_db)

    return pd.concat(instance_dbs)

def segmentations(file_db, archive, pattern_db, mp_db):
    instance_dbs = []
    for corpus_year, package_ids, _ in year_iterator(file_db):
        print("Segmenting year:", corpus_year)
        
        p_pattern_db = pattern_db[pattern_db["start"] <= corpus_year]
        p_pattern_db = pattern_db[pattern_db["end"] >= corpus_year]
        
        p_mp_db = mp_db[mp_db["start"] <= corpus_year]
        p_mp_db = p_mp_db[p_mp_db["end"] >= corpus_year]
        print(p_mp_db)
        
        for protocol_id in progressbar.progressbar(package_ids):
            instance_db = find_instances(protocol_id, archive, p_pattern_db, p_mp_db)
            save_db(instance_db, protocol_id=protocol_id, phase="segmentation")
            instance_dbs.append(instance_db)
    
    return pd.concat(instance_dbs)

def parlaclarin(file_db, archive, curations=None, segmentations=None):
    for corpus_year, package_ids, year_db in year_iterator(file_db):
        print("Generate corpus for year", corpus_year)
        current_instances = pd.merge(segmentations, year_db, on=['protocol_id'])
        current_curations = pd.merge(curations, year_db, on=['protocol_id'])

        corpus_metadata = dict(
            document_title="Riksdagens protocols " + str(corpus_year),
            authority="National Library of Sweden and the WESTAC project",
            correction="Some data curation was done. It is documented in db/curation/instances"
        )
        parla_clarin_str = gen_parlaclarin_corpus(year_db, archive, current_instances, corpus_metadata=corpus_metadata, curation_db=current_curations)
        
        parlaclarin_path = "data/parla-clarin/" + "corpus" + str(corpus_year) + ".xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()

if __name__ == "__main__":
    
    file_db = pd.read_csv("db/protocols/scanned.csv")
    
    start_year = 1920
    end_year = 1990
    
    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    
    mp_db = pd.read_csv("db/mp/members_of_parliament.csv")
    archive = login_to_archive()
    
    if False:
        curation_patterns = load_patterns(phase="curation")
        curation_db = curations(file_db, archive, curation_patterns)
        save_db(curation_db, phase="curation")
    else:
        print("Load curation database...")
        curation_db = load_db(phase="curation")
        print("Done.")
        
    if False:
        segmentation_patterns = load_patterns(phase="segmentation")
        segmentation_db = segmentations(file_db, archive, segmentation_patterns, mp_db)
        save_db(segmentation_db, phase="segmentation")
    else:
        print("Load segmentation database...")
        segmentation_db = load_db(phase="segmentation")
        print("Done.")
    
    if True:
        parlaclarin(file_db, archive, curations=curation_db, segmentations=segmentation_db)



