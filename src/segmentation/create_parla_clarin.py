import pandas as pd
import re
from os import listdir
from os.path import isfile, join
instances_path = "./db/segmentation/instances.json"
instance_db = pd.read_json(instances_path, orient="records", lines=True)

folder = "./data/txt/"
files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]
#files = ["./data/txt/prot_1947__ak__3.txt", "./data/txt/prot_1947__fk__3.txt"]

for filename in files:
    txt = open(filename).read()

instances_path = "./db/segmentation/instances.json"
instance_db.to_json(instances_path, orient="records", lines=True)
