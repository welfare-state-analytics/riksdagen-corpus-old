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
from parliament_data.download import get_blocks, fetch_files, login_to_archive
import hashlib

# Instance detection
def find_instances_xml(root, pattern_db, protocol_id, mp_db=None):
    """
    Find instances of segment start and end patterns in a txt file.

    Args:
        root: root of an lxml tree to be pattern matched.
        pattern_db: Patterns to be matched as a Pandas DataFrame.
    """
    instance_db = pd.DataFrame(columns = ['filename', 'pattern', 'txt'])
    names = []
    if mp_db is not None:
        mp_db = mp_db[mp_db['Riksdagsledamot'].notnull()]
        names = mp_db["Riksdagsledamot"]
        
    for row in pattern_db.iterrows():
        row = row[1]
        pattern = row['pattern']

        #print("PATTERN:", pattern)
        exp = re.compile(pattern)
        #print("EXP", exp)
            
        for content_block in root:
            content_txt = '\n'.join(content_block.itertext())
            
            if not _is_metadata_block(content_txt):
                for m in exp.finditer(content_txt):
                    matched_txt = m.group()
                    person = None
                    for name in names:
                        if name in matched_txt:
                            person = name
                    
                    if person == None:
                        for name in names:
                            if name.upper() in matched_txt:
                                person = name
                            
                    
                    # Only match last name if full name is not found
                    if person == None:
                        for name in names:
                            last_name = name.split()[-1]
                            if last_name in matched_txt:
                                person = name
                            elif last_name.upper() in matched_txt:
                                person = name
                    
                    # Calculate digest for distringuishing patterns without ugly characters
                    pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
                    d = {"filename": protocol_id, "pattern": pattern_digest, "txt": matched_txt, "person": person }
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
    
def _is_metadata_block(txt0):
    txt1 = re.sub("[^a-zA-ZåäöÅÄÖ ]+", "", txt0)
    len0 = len(txt0)
    len1 = len(txt1)
    
    # Crude heuristic. Skip if
    # a) over 15% is non alphabetic characters
    # and b) length is under 150 characters
    
    # TODO: replace with ML algorithm
    return float(len1) / float(len0) < 0.85 and len0 < 150

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
    
def create_parlaclarin(root, metadata, instance_db=pd.DataFrame(columns= ["filename", "pattern", "txt", "person"])):
    """
    Create a Parla-Clarin XML from a list of segments.

    Args:
        txts: a list of lists of strings, corresponds to content blocks and paragraphs, respectively.
        metadata: Metadata of the parliamentary session
    """

    filename = metadata["filename"]
    print("Parla clarin generation, package id", filename)
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
    
    current_speaker = None
    u = etree.SubElement(body_div, "u", who="UNK")
    
    for page in root:
        for content_block in page:
            #print("content_block", content_block)
            content_txt = '\n'.join(content_block.itertext())
            is_data = not _is_metadata_block(content_txt)
            
            if not is_data:
                pass
                #print("Non-data:", content_txt)
            else:
                for textblock in content_block:
                    paragraph = ''.join(textblock.itertext())
                    if paragraph != "":

                        paragraph = textblock.text
                        for ix, match_row in instance_db.iterrows():
                            matchable_txt = match_row["txt"]
                            #print(matchable_txt, type(matchable_txt))
                            if matchable_txt in paragraph:
                                current_speaker = match_row["person"]
                                if type(current_speaker) != str:
                                    current_speaker = None
                                if current_speaker is not None:
                                    u = etree.SubElement(body_div, "u", who=current_speaker)
                                else:
                                    u = etree.SubElement(body_div, "u", who="UNK")
                        seg = etree.SubElement(u, "seg")
                        seg.text = paragraph

    return etree.ElementTree(teiCorpus)

def download_and_convert_to_parlaclarin(package_id, archive, instance_db, str_output=True):
    package = archive.get(package_id)
    metadata = infer_metadata(package_id.replace("-", "_"))
    xml_files = fetch_files(package, return_files=True)
    
    protocol = etree.Element("protocol")

    for xml_file, filename in xml_files:
        page_content_blocks = get_blocks(xml_file)
        protocol.append(page_content_blocks)
    
    parla_clarin = create_parlaclarin(protocol, metadata, instance_db)
    if str_output:
        return etree.tostring(parla_clarin, pretty_print=True, encoding="utf-8", xml_declaration=True).decode("utf-8")
    else:
        return parla_clarin

def instance_workflow(package_id, archive, pattern_db, mp_db):
    package = archive.get(package_id)
    metadata = infer_metadata(package_id.replace("-", "_"))
    year = metadata["year"]
    pattern_db = pattern_db[pattern_db["start"] <= year]
    pattern_db = pattern_db[pattern_db["end"] >= year]
    
    print("Instance detenction, package:", package_id)
    
    mp_db = mp_db[mp_db["start"] <= year]
    mp_db = mp_db[mp_db["end"] >= year]
    
    xml_files = fetch_files(package, return_files=True)
    instance_dbs = []

    for xml_file, filename in xml_files:
        page_content_blocks = get_blocks(xml_file)
        instance_db = find_instances_xml(page_content_blocks, pattern_db, package_id, mp_db=mp_db)
        instance_dbs.append(instance_db)
    
    instance_db = pd.concat(instance_dbs)
    instance_db["filename"] = package_id
    return instance_db
    
