import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from lxml import etree

instances_path = "./db/segmentation/instances.json"
instance_db = pd.read_json(instances_path, orient="records", lines=True)

folder = "./data/txt/"
files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]
#files = ["./data/txt/prot_1947__ak__3.txt", "./data/txt/prot_1947__fk__3.txt"]

def split_by_indices(s, indices):
    indices = sorted(indices)
    parts = [s[i:j] for i,j in zip([0] + indices, indices+[-1])]
    return parts

xml_folder = "./data/xml/"

for filename in files:
    txt = open(filename).read()

    filename = filename.split("/")[-1]
    instances = instance_db.loc[instance_db['filename'] == filename]

    print(instances)

    indices = instances['loc']
    indices = sorted(list(indices))

    print(indices)

    txts = split_by_indices(txt, indices)


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




    tree = etree.ElementTree(teiCorpus)

    filepath = xml_folder + filename.replace(".txt", ".xml")
    et = etree.ElementTree(teiCorpus)
    et.write(filepath, encoding="utf-8", pretty_print=True)

