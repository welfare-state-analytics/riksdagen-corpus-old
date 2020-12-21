"""
Implements the segmentation of the data into speeches and
ultimately into the Parla-Clarin XML format.
"""

import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from lxml import etree
from parliament_data.mp import detect_mp

# Instance detection
def find_instances_txt(filename, pattern_db):
    """
    Find instances of segment start and end patterns in a txt file.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        filename: Path to file to be searched.
    """
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
    """
    Find instances of segment start and end patterns in an html file.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        filename: Path to file to be searched.
    """
    # TODO: implement
    columns = ['filename', 'loc', 'pattern', 'txt']
    instance_db = pd.DataFrame(columns = columns) 
    return instance_db

# Segmentation
def find_instances(folder, pattern_db):
    """
    Find instances of segmentation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """
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

def _detect_name(s):
    s = s.split(":")[0]
    s = s.split(".")[0]
    words = s.split()
    lowercase_words = s.lower().split()

    output = []
    for word in words:
        if word not in lowercase_words:
            output.append(word)

    return " ".join(output)

def _metadata(filename):
    metadata = dict()
    txt = open(filename).read()

    metadata["filename"] = filename.split("/")[-1].split(".")[0]
    split = filename.split("/")[-1].split("_")

    # Year
    for s in split:
        s = s[:4]
        if s.isdigit():
            year = int(s)
            if year > 1800 and year < 2100:
                metadata["year"] = year

    # Chamber
    metadata["chamber"] = None
    if "_ak_" in filename:
        metadata["chamber"] = "ak"
    elif "_fk_" in filename:
        metadata["chamber"] = "fk"

    # TODO: Month and day
    metadata["date"] = "1.1.2021"

    # TODO: Day of the week
    metadata["weekday"] = "Tuesday"

    return metadata

def segment(filename, instance_db):
    """
    Create a Parla-Clarin XML of a file.

    Args:
        filename: Path to file to be converted.
        instance_db: Instances of matched patterns as a Pandas DataFrame.
    """
    txt = open(filename).read()
    
    # Get rid of extra line breaks within paragraphs
    file_metadata = _metadata(filename)

    print("Metadata", file_metadata)
    
    filename = filename.split("/")[-1]
    instances = instance_db.loc[instance_db['filename'] == filename]

    indices = instances['loc']
    indices = sorted(list(indices))

    txts = _split_by_indices(txt, indices)

    return txts

def create_parlaclarin(txts, metadata):
    """
    Create a Parla-Clarin XML from a list of segments.

    Args:
        txts: a list of lists of strings, corresponds to content blocks and paragraphs, respectively.
        metadata: Metadata of the parliamentary session
    """

    filename = metadata["filename"]
    # Create element tree for the file
    teiCorpus = etree.Element("teiCorpus")
    tei = etree.SubElement(teiCorpus, "TEI")

    teiHeader = etree.SubElement(tei, "teiHeader")

    text = etree.SubElement(tei, "text")
    front = etree.SubElement(text, "front")
    preface = etree.SubElement(front, "div", type="preface")
    etree.SubElement(preface, "head").text = filename.split(".")[0]
    etree.SubElement(preface, "docDate", when=metadata["date"]).text = metadata["date"]

    body = etree.SubElement(text, "body")
    body_div = etree.SubElement(body, "div")
    
    for content_block in txts:

        for speech in content_block:
            speech = re.sub('([a-zäö,])\n ?([a-zäö])', '\\1 \\2', speech)
            intro = speech[:100]
            name = _detect_name(intro)

            if name != "":
                u = etree.SubElement(body_div, "u", who=name)
                for speech_line in speech.split("\n"):
                    speech_line = speech_line.strip()
                    if speech_line != "":
                        seg = etree.SubElement(u, "seg")
                        seg.text = speech_line

                intro = speech[:100]
                name = _detect_name(intro)

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
