from riksdagen_corpus.db import filter_db, load_patterns
from riksdagen_corpus.refine import detect_mps, find_introductions, format_texts
from riksdagen_corpus.utils import infer_metadata
from lxml import etree
import pandas as pd

protocol_id = "prot-1955-höst-ak--29"
metadata = infer_metadata(protocol_id)
s = open("data/new-parlaclarin/" + protocol_id + ".xml").read().encode("utf-8")
root = etree.fromstring(s)
print(root)


mp_db = pd.read_csv("db/mp/members_of_parliament.csv")
mp_db = filter_db(mp_db, year=1955)
names = mp_db["name"]
ids = mp_db["id"]
names_ids = list(zip(names,ids))

pattern_db = load_patterns()
root = find_introductions(root,pattern_db, names_ids)
root = detect_mps(root,names_ids)
#root = format_texts(root)

b = etree.tostring(root, pretty_print=True, encoding="utf-8")

f = open("output.xml", "wb")
f.write(b)
f.close()