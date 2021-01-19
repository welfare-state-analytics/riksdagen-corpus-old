"""
Provides useful utilities for the other modules as well as for general use.
"""

import lxml
from lxml import etree
import xml.etree.ElementTree as et
import sys, re, os
from bs4 import BeautifulSoup
import pandas as pd

def infer_metadata(filename):
    metadata = dict()
    filename = filename.replace("-", "_")
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
    metadata["chamber"] = "Enkammarriksdagen"
    if "_ak_" in filename:
        metadata["chamber"] = "Andra kammaren"
    elif "_fk_" in filename:
        metadata["chamber"] = "Första kammaren"
    
    metadata["number"] = int(split[-1])
    return metadata

def _clean_html(raw_html):
    # Clean the HTML code in the Riksdagen XML text format
    raw_html = raw_html.replace("\n", " NEWLINE ")
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace(" NEWLINE ", "\n")
    return cleantext

def read_riksdagen_xml(path):
    """
    Read Riksdagen XML text format and return a tuple
    consisting of an etree of , as well as the HTML
    inside the text element
    """
    # TODO: implement

    xml, cleaned_html

def read_html(path):
    """
    Read a HTML file and turn it into valid XML
    """
    f = open(path)
    soup = BeautifulSoup(f)
    f.close()
    pretty_html = soup.prettify()
    return etree.fromstring(pretty_html)
    
def validate_xml_schema(xml_path, schema_path):
    xml_file = lxml.etree.parse(xml_path)

    schema = lxml.etree.XMLSchema(file=schema_path)
    is_valid = schema.validate(xml_file)

    return is_valid


def parlaclarin_to_md(tree):
    """
    Convert Parla-Clarin XML to markdown. Returns a string.
    """
    return ""

def parlaclarin_to_txt(tree):
    """
    Convert Parla-Clarin XML to plain text. Returns a string.
    """
    segments = tree.findall('.//seg')

    for segment in segments:
    	etree.strip_tags(segment, 'seg')
    	#print(type(segment))
    #return 
    segment_txts = [etree.tostring(segment, pretty_print=True, encoding="UTF-8").decode("utf-8") for segment in segments]
    segment_txts = [txt.replace("<seg>", "").replace("</seg>", "") for txt in segment_txts]

    print(segment_txts[0])
    print(type(segment_txts[0]))

    return "\n".join(segment_txts)

def speeches_with_name(tree, name):
    """
    Convert Parla-Clarin XML to plain text. Returns a string.
    """
    us = tree.findall('.//u')

    texts = []
    for u in us:
        if name.lower() in u.attrib['who'].lower():
            text = etree.tostring(u, pretty_print=True, encoding="UTF-8").decode("utf-8")
            texts.append(text)
        #print(type(segment))
    return texts

if __name__ == '__main__':
    validate_parla_clarin_example()
    #update_test()
