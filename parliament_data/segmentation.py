import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from lxml import etree

# Instance detection
def find_instances_txt(filename, pattern_db):
    instance_db = pd.DataFrame(columns = ['filename', 'loc', 'pattern', 'txt']) 
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

    return instance_db

def find_instances_html(filename, pattern_db):
    # TODO: implement
    columns = ['filename', 'loc', 'pattern', 'txt']
    instance_db = pd.DataFrame(columns = columns) 
    return instance_db

# Segmentation
def find_instances(folder, pattern_db):
    files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]

    instance_dbs = []
    for filename in files:
        extension = filename.split(".")[-1]
        if extension == "txt":
            instance_db = find_instances_txt(filename, pattern_db)
            instance_dbs.append(instance_db)
        elif extension == "html":
            instance_db = find_instances_html(filename, pattern_db)
            instance_dbs.append(instance_db)

    return pd.concat(instance_dbs, sort=False)

# Parla Clarin generation
def _split_by_indices(s, indices):
    indices = sorted(indices)
    parts = [s[i:j] for i,j in zip([0] + indices, indices+[-1])]
    return parts

def create_parlaclarin(filename, instance_db):
    txt = open(filename).read()

    filename = filename.split("/")[-1]
    instances = instance_db.loc[instance_db['filename'] == filename]

    indices = instances['loc']
    indices = sorted(list(indices))

    txts = _split_by_indices(txt, indices)

    # Create element tree for the file
    teiCorpus = etree.Element("teiCorpus")
    tei = etree.SubElement(teiCorpus, "TEI")

    teiHeader = etree.SubElement(tei, "teiHeader")

    text = etree.SubElement(tei, "text")
    front = etree.SubElement(text, "front")
    preface = etree.SubElement(front, "div", type="preface")
    etree.SubElement(preface, "head").text = filename.split(".")[0]
    etree.SubElement(preface, "docDate", when="2011-01-30").text = "30th January 2011"

    body = etree.SubElement(text, "body")
    body_div = etree.SubElement(body, "div")
    
    for speech in txts:
        u = etree.SubElement(body_div, "u")
        for speech_line in speech.split("\n"):
            speech_line = speech_line.strip()
            if speech_line != "":
                seg = etree.SubElement(u, "seg")
                seg.text = speech_line

    return etree.ElementTree(teiCorpus)

# Scripts
def instance_workflow():
    pattern_path = "./db/segmentation/patterns.json"
    pattern_db = pd.read_json(pattern_path, orient="records", lines=True)

    folder = "./data/txt/"
    instance_db = find_instances(folder, pattern_db)
    print(instance_db)

    instances_path = "./db/segmentation/instances.json"
    instance_db.to_json(instances_path, orient="records", lines=True)

def parlaclarin_workflow():
    instances_path = "./db/segmentation/instances.json"
    instance_db = pd.read_json(instances_path, orient="records", lines=True)

    folder = "./data/txt/"
    xml_folder = "./data/xml-output/"
    files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]
    for filename in files:
        element_tree = create_parlaclarin(filename, instance_db)
        filepath = xml_folder + filename.split("/")[-1].replace(".txt", ".xml")
        print(filepath)
        element_tree.write(filepath, encoding="utf-8", pretty_print=True)

if __name__ == '__main__':
    instance_workflow()
    parlaclarin_workflow()
