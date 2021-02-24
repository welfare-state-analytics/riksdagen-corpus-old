from riksdagen_corpus.db import filter_db, load_patterns
from riksdagen_corpus.refine import detect_mps, find_introductions, format_texts, update_ids
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
    root = etree.parse(filename, parser).getroot()

    year = metadata["year"]
    #print(year, type(year))
    years = [int(elem.attrib.get("when").split("-")[0]) for elem in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate")]

    if not year in years:
        year = years[0]

    if str(year) not in protocol_id:
        print(protocol_id, year)
    year_mp_db = filter_db(mp_db, year=year)
    names = year_mp_db["name"]
    ids = year_mp_db["id"]
    names_ids = list(zip(names,ids))

    pattern_db = load_patterns()
    root = find_introductions(root,pattern_db,names_ids)
    root = detect_mps(root,names_ids,pattern_db)
    root = format_texts(root)
    root = update_ids(root, protocol_id)
    b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

    f = open(pc_folder + protocol_id + ".xml", "wb")
    f.write(b)
    f.close()