from riksdagen_corpus.db import filter_db, load_patterns
from riksdagen_corpus.refine import detect_date
from riksdagen_corpus.utils import infer_metadata
from lxml import etree
import pandas as pd
import os
import progressbar

pc_folder = "data/new-parlaclarin/"
protocol_ids = os.listdir(pc_folder)
protocol_ids = [protocol_id.replace(".xml", "") for protocol_id in protocol_ids if protocol_id.split(".")[-1] == "xml"]

mp_db = pd.read_csv("db/mp/members_of_parliament.csv")

parser = etree.XMLParser(remove_blank_text=True)
for protocol_id in progressbar.progressbar(protocol_ids):
    metadata = infer_metadata(protocol_id)
    filename = pc_folder + protocol_id + ".xml"
    
    root = etree.parse(filename, parser)
    root, dates = detect_date(root, metadata["year"])

    b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

    f = open(filename, "wb")
    f.write(b)
    f.close()
    