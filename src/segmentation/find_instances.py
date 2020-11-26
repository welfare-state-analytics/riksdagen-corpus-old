import pandas as pd
import re
from os import listdir
from os.path import isfile, join
pattern_path = "./db/segmentation/patterns.json"
pattern_db = pd.read_json(pattern_path, orient="records", lines=True)

instance_db = pd.DataFrame(columns = ['pattern', 'loc', 'txt']) 

folder = "./data/txt/"
files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]
#files = ["./data/txt/prot_1947__ak__3.txt", "./data/txt/prot_1947__fk__3.txt"]

for filename in files:
    txt = open(filename).read()

    for row in pattern_db.iterrows():
        row = row[1]
        pattern = row['pattern']

        print("PATTERN:", pattern)
        exp = re.compile(pattern)
        print("EXP", exp)
        log_fname = filename.split("/")[-1]
        for m in exp.finditer(txt):
            d = {"filename": log_fname, "pattern": pattern, "loc": m.start(), "txt":m.group()}
            instance_db = instance_db.append(d, ignore_index=True)


    print(instance_db)

instances_path = "./db/segmentation/instances.json"
instance_db.to_json(instances_path, orient="records", lines=True)
