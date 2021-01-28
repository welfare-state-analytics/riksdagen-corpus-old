"""
Parla Clarin generation
"""
import pandas as pd
import progressbar, copy
from lxml import etree
from riksdagen_corpus.utils import infer_metadata
from riksdagen_corpus.download import get_blocks, fetch_files, login_to_archive
from riksdagen_corpus.curation import apply_curations
from riksdagen_corpus.segmentation import apply_instances

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
    
def create_tei(root, metadata):
    """
    Create a Parla-Clarin TEI element from a list of segments.

    Args:
        txts: a list of lists of strings, corresponds to content blocks and paragraphs, respectively.
        metadata: Metadata of the parliamentary session
    """
    metadata = copy.deepcopy(metadata)
    
    tei = etree.Element("TEI")
    protocol_id = root.attrib["id"]
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
    u = None
    
    for content_block in root:
        content_txt = '\n'.join(content_block.itertext())
        is_empty = content_txt == ""
        cb_ix = content_block.attrib["ix"]
        segmentation = content_block.attrib.get("segmentation", None)
        if segmentation == "metadata":
            pass
            #print("Empty block")
        else:
            for textblock in content_block:
                tb_segmentation = textblock.attrib.get("segmentation", None)
                if tb_segmentation == "speech_start":
                    current_speaker = textblock.attrib.get("who", None)
                    note = etree.SubElement(body_div, "note", type="speaker")                    
                    u = etree.SubElement(body_div, "u")
                    if current_speaker is not None:
                        u.attrib["who"] = current_speaker
                    u.attrib["{http://www.w3.org/XML/1998/namespace}id"] = textblock.attrib.get("id", None)
                    seg = etree.SubElement(u, "seg")

                    # Introduction under <note> tag
                    # Actual speech under <u> tag
                    paragraph = textblock.text.split(":")
                    introduction = paragraph[0] + ":"
                    note.text = introduction
                    if len(paragraph) > 1:
                        seg.text = ":".join(paragraph[1:]).strip()
                elif tb_segmentation == "description_start":
                    u = None
                    current_speaker = None
                else:
                    paragraph = textblock.text
                    tb_segmentation = textblock.attrib.get("segmentation", None)
                    if paragraph != "" and tb_segmentation != "metadata":
                        if u is not None:
                            seg = etree.SubElement(u, "seg")
                            seg.text = paragraph
                        else:
                            note = etree.SubElement(body_div, "note")
                            note.text = paragraph
    return tei

def gen_parlaclarin_corpus(protocol_db, archive, instance_db, curation_db=None, corpus_metadata=dict(), str_output=True):
    teis = []
    print("Pages in total", protocol_db["pages"].sum())
    
    for ix, package in progressbar.progressbar(list(protocol_db.iterrows())):
        protocol_id = package["protocol_id"]
        pages = package["pages"]
        metadata = infer_metadata(protocol_id)
        protocol = get_blocks(protocol_id, archive)
        protocol = apply_curations(protocol, curation_db)
        protocol = apply_instances(protocol, instance_db)
        tei = create_tei(protocol, metadata)
        teis.append(tei)
    
    corpus_metadata["edition"] = "0.1.0"
    corpus = create_parlaclarin(teis, corpus_metadata)
    return corpus
