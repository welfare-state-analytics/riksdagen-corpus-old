import pandas as pd
import os
import progressbar

from riksdagen_corpus.download import LazyArchive
from riksdagen_corpus.segmentation import find_instances
from riksdagen_corpus.curation import curation_workflow
from riksdagen_corpus.export import gen_parlaclarin_corpus
from riksdagen_corpus.utils import infer_metadata
from riksdagen_corpus.db import load_db, save_db, load_patterns, year_iterator

def filter_db(db, year=None, protocol_id=None):
    assert year is not None or protocol_id is not None, "Provide either year or protocol id"
    if year is not None:
        filtered_db = db[db["start"] <= year]
        filtered_db = filtered_db[filtered_db["end"] >= year]
        return filtered_db
    else:
        return db[db["protocol_id"] == protocol_id]

def curations(file_db, archive, pattern_db):
    instance_dbs = []
    for corpus_year, package_ids, _ in year_iterator(file_db):
        print("Curating year:", corpus_year)
        
        year_patterns = filter_db(pattern_db, year=corpus_year)
        print(pattern_db_i)

        for protocol_id in progressbar.progressbar(package_ids):
            protocol_patterns = filter_db(pattern_db, protocol_id=protocol_id)
            protocol_patterns = pd.concat([protocol_patterns, year_patterns])
            instance_db = curation_workflow(protocol_id, archive, protocol_patterns)
            instance_dbs.append(instance_db)

    print(pd.concat(instance_dbs))
    return pd.concat(instance_dbs)

def segmentations(file_db, archive, pattern_db, mp_db):
    import tensorflow as tf
    import fasttext.util

    model = tf.keras.models.load_model("segment-classifier")
    ft = fasttext.load_model('cc.sv.300.bin')

    classifier = dict(
        model=model,
        ft=ft,
        dim=ft.get_word_vector("hej").shape[0]
    )
    #classifier = None

    instance_dbs = []
    for corpus_year, package_ids, _ in year_iterator(file_db):
        print("Segmenting year:", corpus_year)
        
        year_patterns = filter_db(pattern_db, year=corpus_year)
        year_mps = filter_db(mp_db, year=corpus_year)
        
        for protocol_id in progressbar.progressbar(package_ids):
            protocol_patterns = filter_db(pattern_db, protocol_id=protocol_id)
            protocol_patterns = pd.concat([protocol_patterns, year_patterns])
            instance_db = find_instances(protocol_id, archive, protocol_patterns, year_mps, classifier=classifier)
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
    
    file_dbs = []
    file_dbs.append(pd.read_csv("db/protocols/scanned.csv"))
    file_dbs.append(pd.read_csv("db/protocols/digital_originals.csv"))
    file_db = pd.concat(file_dbs)
    
    start_year = 1920
    end_year = 2021

    start_year = 1920
    end_year = 1921
    
    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    
    mp_db = pd.read_csv("db/mp/members_of_parliament.csv")
    archive = LazyArchive()
    
    if False:
        curation_patterns = load_patterns(phase="curation")
        curation_db = curations(file_db, archive, curation_patterns)
        save_db(curation_db, phase="curation")
    else:
        print("Load curation database...")
        curation_db = load_db(phase="curation")
        print("Done.")
        
    if True:
        segmentation_patterns = load_patterns(phase="segmentation")
        segmentation_db = segmentations(file_db, archive, segmentation_patterns, mp_db)
        save_db(segmentation_db, phase="segmentation")
    else:
        print("Load segmentation database...")
        segmentation_db = load_db(phase="segmentation")
        print("Done.")
    
    if False:
        parlaclarin(file_db, archive, curations=curation_db, segmentations=segmentation_db)



