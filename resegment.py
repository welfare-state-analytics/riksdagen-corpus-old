from riksdagen_corpus.db import filter_db, load_patterns
from riksdagen_corpus.refine import detect_mps, find_introductions, format_texts
from riksdagen_corpus.utils import infer_metadata
from lxml import etree
import pandas as pd
import os
import progressbar

protocol_ids = ["prot-1955-höst-ak--29"]
pc_folder = "data/new-parlaclarin/"
protocol_ids = os.listdir(pc_folder)
protocol_ids = [protocol_id.replace(".xml", "") for protocol_id in protocol_ids if protocol_id.split(".")[-1] == "xml"]

mp_db = pd.read_csv("db/mp/members_of_parliament.csv")

for protocol_id in progressbar.progressbar(protocol_ids):
    metadata = infer_metadata(protocol_id)
    
    s = open(pc_folder + protocol_id + ".xml").read().encode("utf-8")
    root = etree.fromstring(s)

    year = metadata["year"]
    year_mp_db = filter_db(mp_db, year=year)
    names = year_mp_db["name"]
    ids = year_mp_db["id"]
    names_ids = list(zip(names,ids))

    pattern_db = load_patterns()
    root = find_introductions(root,pattern_db,names_ids)
    #root = detect_mps(root,names_ids)
    #root = format_texts(root)

    b = etree.tostring(root, pretty_print=True, encoding="utf-8")

    f = open(pc_folder + protocol_id + ".xml", "wb")
    f.write(b)
    f.close()