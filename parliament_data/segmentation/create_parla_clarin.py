import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from lxml import etree

def _split_by_indices(s, indices):
    indices = sorted(indices)
    parts = [s[i:j] for i,j in zip([0] + indices, indices+[-1])]
    return parts

def create_parlaclarin(filename):
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

if __name__ == '__main__':
    instances_path = "./db/segmentation/instances.json"
    instance_db = pd.read_json(instances_path, orient="records", lines=True)

    folder = "./data/txt/"
    xml_folder = "./data/xml-output/"
    files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]
    for filename in files:
        element_tree = create_parlaclarin(filename)
        filepath = xml_folder + filename.split("/")[-1].replace(".txt", ".xml")
        print(filepath)
        element_tree.write(filepath, encoding="utf-8", pretty_print=True)
