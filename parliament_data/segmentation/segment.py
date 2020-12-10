import pandas as pd
import re
from os import listdir
from os.path import isfile, join

def segment_txt(filename, pattern_db):
    txt = open(filename).read()

    columns = ['filename', 'loc', 'pattern', 'txt']
    instance_db = pd.DataFrame(columns = columns) 
    
    for row in pattern_db.iterrows():
        row = row[1]
        pattern = row['pattern']

        print("PATTERN:", pattern)
        exp = re.compile(pattern)
        print("EXP", exp)
        log_fname = filename.split("/")[-1]
        for m in exp.finditer(txt):
            d = {"filename": log_fname, "loc": m.start(), "pattern": pattern, "txt":m.group()}
            instance_db = instance_db.append(d, ignore_index=True)

    return instance_db
    
def segment_html(filename, pattern_db):
    columns = ['filename', 'loc', 'pattern', 'txt']
    instance_db = pd.DataFrame(columns = columns) 
    return instance_db

def segment_files(folder, pattern_db):
    files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]

    instance_dbs = []
    for filename in files:
        extension = filename.split(".")[-1]
        if extension == "txt":
            instance_db = segment_txt(filename, pattern_db)
            instance_dbs.append(instance_db)
        elif extension == "html":
            instance_db = segment_html(filename, pattern_db)
            instance_dbs.append(instance_db)

    return pd.concat(instance_dbs, sort=False)

if __name__ == "__main__":
    pattern_path = "./db/segmentation/patterns.json"
    pattern_db = pd.read_json(pattern_path, orient="records", lines=True)
    folder = "./data/txt/"

    instance_db = segment_files(folder, pattern_db)
    print(instance_db)
    instances_path = "./db/segmentation/instances.json"
    instance_db.to_json(instances_path, orient="records", lines=True)
