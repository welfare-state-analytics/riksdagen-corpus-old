import xml.etree.ElementTree as et
import sys
import pandas as pd


db_path = "db/curation/types.json"
xml_path = sys.argv[1]
#tree = et.parse(xml_path)
#root = tree.getroot()

print(root)

db = pd.read_json(db_path, orient="records", lines=True)
print(db)