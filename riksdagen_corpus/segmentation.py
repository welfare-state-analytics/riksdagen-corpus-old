"""
Implements the segmentation of the data into speeches and
ultimately into the Parla-Clarin XML format.
"""

import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from lxml import etree
from riksdagen_corpus.mp import detect_mp
from riksdagen_corpus.download import get_blocks, fetch_files, login_to_archive
from riksdagen_corpus.curation import get_curated_blocks
import hashlib
import copy

def _is_metadata_block(txt0):
    txt1 = re.sub("[^a-zA-ZåäöÅÄÖ ]+", "", txt0)
    len0 = len(txt0)
    if len0 == 0:
        return False
        
    len1 = len(txt1)
    len2 = len(txt0.strip())
    if len2 == 0:
        return False
    
    # Crude heuristic. Skip if
    # a) over 15% is non alphabetic characters
    # and b) length is under 150 characters
    
    # TODO: replace with ML algorithm
    return float(len1) / float(len0) < 0.85 and len0 < 150
    
# Instance detection
def find_instances_xml(root, pattern_db, protocol_id, mp_db=None):
    """
    Find instances of segment start and end patterns in a txt file.

    Args:
        root: root of an lxml tree to be pattern matched.
        pattern_db: Patterns to be matched as a Pandas DataFrame.
    """
    columns = ['package_id', 'pattern', 'txt', "person"]
    data = []
    names = []
    if mp_db is not None:
        mp_db = mp_db[mp_db['name'].notnull()]
        names = mp_db["name"]
        
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
                            last_name = " " + name.split()[-1]
                            if last_name in matched_txt:
                                person = name
                            elif last_name.upper() in matched_txt:
                                person = name
                    
                    # Calculate digest for distringuishing patterns without ugly characters
                    pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
                    d = {"package_id": protocol_id, "pattern": pattern_digest, "txt": matched_txt, "person": person }
                    data.append(d)

    return  pd.DataFrame(data, columns=columns)

def find_instances_html(filename, pattern_db):
    """
    Find instances of segment start and end patterns in an html file (digital originals).

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        filename: Path to file to be searched.
    """
    # TODO: implement
    columns = ['filename', 'loc', 'pattern', 'txt']
    instance_db = pd.DataFrame(columns = columns) 
    return instance_db

# Parla Clarin generation
def infer_metadata(filename):
    metadata = dict()

    metadata["protocol"] = filename.split("/")[-1].split(".")[0]
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
    # TODO: Day of the week
    print("Metadata", metadata)
    return metadata

# Generate parla clarin header
def _pc_header(metadata):
    teiHeader = etree.Element("teiHeader")
    
    # fileDesc
    fileDesc = etree.SubElement(teiHeader, "fileDesc")
    
    titleStmt = etree.SubElement(fileDesc, "titleStmt")
    title = etree.SubElement(titleStmt, "title")
    title.text = metadata.get("document_title", "N/A")
    
    if "edition" in metadata:
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
    
    return teiHeader
    
def create_parlaclarin(teis, metadata):
    if type(teis) != list:
        tei = teis
        return create_parlaclarin([tei], metadata)
    
    teiCorpus = etree.Element("teiCorpus", xmlns="http://www.tei-c.org/ns/1.0")
    teiHeader = _pc_header(metadata)
    teiCorpus.append(teiHeader)
    
    for tei in teis:
        teiCorpus.append(tei)
    
    teiCorpusTree = etree.ElementTree(teiCorpus)
    
    for xml_element in teiCorpusTree.iter():
        content = xml_element.xpath('normalize-space()')
        if not content:
            xml_element.getparent().remove(xml_element)
            
    s = etree.tostring(teiCorpusTree, pretty_print=True, encoding="utf-8", xml_declaration=True).decode("utf-8")
    return s
    
def create_tei(root, metadata, instance_db=pd.DataFrame(columns= ["package_id", "pattern", "txt", "person"])):
    """
    Create a Parla-Clarin TEI element from a list of segments.

    Args:
        txts: a list of lists of strings, corresponds to content blocks and paragraphs, respectively.
        metadata: Metadata of the parliamentary session
    """
    metadata = copy.deepcopy(metadata)
    
    tei = etree.Element("TEI")
    protocol_id = metadata["protocol"]
    metadata["document_title"] = protocol_id.replace("_", " ").split("-")[0].replace("prot", "Protokoll")
    documentHeader = _pc_header(metadata)
    tei.append(documentHeader)
    
    text = etree.SubElement(tei, "text")
    front = etree.SubElement(text, "front")
    preface = etree.SubElement(front, "div", type="preface")
    etree.SubElement(preface, "head").text = protocol_id.split(".")[0]
    if "date" not in metadata:
        year = metadata.get("year", 2020)
        metadata["date"] = str(year) + "-01-01"
        
    etree.SubElement(preface, "docDate", when=metadata["date"]).text = metadata.get("date", "2020-01-01")

    body = etree.SubElement(text, "body")
    body_div = etree.SubElement(body, "div")
    
    current_speaker = None
    u = etree.SubElement(body_div, "u", who="UNK")
    
    instance_rows = list(instance_db.iterrows())
    for content_block in root.findall(".//contentBlock"):
        content_txt = '\n'.join(content_block.itertext())
        is_empty = content_txt == ""
        
        if is_empty:
            pass
            #print("Empty block")
        else:
            for textblock in content_block:
                #paragraph = ''.join(textblock.itertext())
                paragraph = textblock.text
                if paragraph != "":
                    for ix, match_row in instance_rows:
                        matchable_txt = match_row["txt"]
                        
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
    
    return tei

def gen_parlaclarin_corpus(protocol_db, archive, instance_db, curation_instance_db=None, corpus_metadata=dict(), str_output=True):
    teis = []
    
    print("Pages in total", protocol_db["pages"].sum())
    
    for ix, package in protocol_db.iterrows():
        package_id = package["package_id"]
        pages = package["pages"]
        print("Create TEI for", package_id, ", pages", pages)
        package = archive.get(package_id)
        metadata = infer_metadata(package_id.replace("-", "_"))
        xml_files = fetch_files(package)
        
        protocol = get_blocks(package, package_id)
        
        current_instances = instance_db[instance_db["package_id"] == package_id]
        print("create tei")
        tei = create_tei(protocol, metadata, instance_db=current_instances)
        teis.append(tei)
    
    corpus_metadata["edition"] = "0.1.0"
    corpus = create_parlaclarin(teis, corpus_metadata)
    return corpus

def instance_workflow(package_id, archive, pattern_db, mp_db):
    package = archive.get(package_id)
    
    xml_files = fetch_files(package)
    page_content_blocks = get_blocks(package, package_id)
    instance_db = find_instances_xml(page_content_blocks, pattern_db, package_id, mp_db=mp_db)
    
    instance_db["package_id"] = package_id
    return instance_db
    
