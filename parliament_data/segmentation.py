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
from parliament_data.download.count_pages import get_blocks
from parliament_data.download.generate_sets import fetch_files

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

def infer_metadata(filename):
    metadata = dict()

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
    metadata["date"] = "2021-01-01"

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
    file_metadata = infer_metadata(filename)

    print("Metadata", file_metadata)
    
    filename = filename.split("/")[-1]
    instances = instance_db.loc[instance_db['filename'] == filename]

    indices = instances['loc']
    indices = sorted(list(indices))

    txts = _split_by_indices(txt, indices)

    return txts

# Generate parla clarin header
def _pc_header(metadata):
    teiHeader = etree.Element("teiHeader")
    
    # fileDesc
    fileDesc = etree.SubElement(teiHeader, "fileDesc")
    
    titleStmt = etree.SubElement(fileDesc, "titleStmt")
    title = etree.SubElement(titleStmt, "title")
    title.text = metadata.get("document_title", "N/A")
    
    editionStmt = etree.SubElement(fileDesc, "editionStmt")
    edition = etree.SubElement(editionStmt, "edition")
    edition.text = metadata.get("edition", "N/A")
    
    extent = etree.SubElement(fileDesc, "extent")
    publicationStmt = etree.SubElement(fileDesc, "publicationStmt")
    authority = etree.SubElement(publicationStmt, "authority")
    authority.text = metadata.get("authority", "N/A")
    
    sourceDesc = etree.SubElement(fileDesc, "sourceDesc")
    sourceBibl = etree.SubElement(sourceDesc, "bibl")
    sourceTitle = etree.SubElement(sourceBibl, "title")
    sourceTitle.text = metadata.get("document_title", "N/A")
    
    # encodingDesc
    encodingDesc = etree.SubElement(teiHeader, "encodingDesc")
    editorialDecl = etree.SubElement(encodingDesc, "editorialDecl")
    correction = etree.SubElement(editorialDecl, "correction")
    correction_p = etree.SubElement(correction, "p")
    correction_p.text = metadata.get("correction", "No correction of source texts was performed.")

    # profileDesc
    #profileDesc = etree.SubElement(teiHeader, "profileDesc")
    #settingDesc = etree.SubElement(profileDesc, "settingDesc")
    #particDesc = etree.SubElement(profileDesc, "particDesc")
    #langUsage = etree.SubElement(profileDesc, "langUsage")
    
    return teiHeader
    
def create_parlaclarin(txts, metadata):
    """
    Create a Parla-Clarin XML from a list of segments.

    Args:
        txts: a list of lists of strings, corresponds to content blocks and paragraphs, respectively.
        metadata: Metadata of the parliamentary session
    """

    filename = metadata["filename"]
    # Create element tree for the file
    teiCorpus = etree.Element("teiCorpus", xmlns="http://www.tei-c.org/ns/1.0")
    teiHeader = _pc_header(metadata)
    
    teiCorpus.append(teiHeader)
    tei = etree.SubElement(teiCorpus, "TEI")

    documentHeader = _pc_header(metadata)
    tei.append(documentHeader)
    
    text = etree.SubElement(tei, "text")
    front = etree.SubElement(text, "front")
    preface = etree.SubElement(front, "div", type="preface")
    etree.SubElement(preface, "head").text = filename.split(".")[0]
    etree.SubElement(preface, "docDate", when=metadata["date"]).text = metadata.get("date", "2020-01-01")

    body = etree.SubElement(text, "body")
    body_div = etree.SubElement(body, "div")
    
    for content_block in txts:
        #print(content_block)
        first_speech = content_block[0]
        first_speech = re.sub('([a-zäö,])\n ?([a-zäö])', '\\1 \\2', first_speech)
        intro = first_speech[:100]
        name = _detect_name(intro)

        if name != "":
            u = etree.SubElement(body_div, "u", who=name)
        else:
            u = etree.SubElement(body_div, "u")

        for speech in content_block:
            for speech_line in speech.split("\n"):
                speech_line = speech_line.strip()
                if speech_line != "":
                    seg = etree.SubElement(u, "seg")
                    seg.text = speech_line


    return etree.ElementTree(teiCorpus)

def download_and_convert_to_parlaclarin(package_id, archive, str_output=True):
    package = archive.get(package_id)
    metadata = infer_metadata(package_id.replace("-", "_"))
    xml_files = fetch_files(package, return_files=True)
    content_blocks = []

    for xml_file, filename in xml_files:
        page_content_blocks = get_blocks(xml_file)
        content_blocks = content_blocks + page_content_blocks
    
    parla_clarin = create_parlaclarin(content_blocks, metadata)
    if str_output:
        return etree.tostring(parla_clarin, pretty_print=True, encoding="utf-8", xml_declaration=True).decode("utf-8")
    else:
        return parla_clarin

if __name__ == '__main__':
    instance_workflow()
    parlaclarin_workflow()
