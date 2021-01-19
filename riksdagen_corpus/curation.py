"""
Provides functions for the curation of the parliamentary data.
"""

import pandas as pd
import re, hashlib
from os import listdir
from lxml import etree
from os.path import isfile, join
from riksdagen_corpus.download import get_blocks, fetch_files, login_to_archive

def _langmod_loss(sentence):
    return 0.0

def improvement(sentence, regexp):
    """
    Calculates the improvement in probability for a suggested text edit. Returns a tuple of losses.
    """
    sentence_suggestion = regexp
    loss0 = _langmod_loss(sentence)
    loss1 = _langmod_loss(sentence_suggestion)

    return loss0, loss1
    
def find_instances(root, pattern_db, c_hashes = dict()):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """
    columns=["pattern", "txt", "replacement"]
    data = []
    protocol_id = root.attrib["id"]
    expressions = dict()
    for _, row in pattern_db.iterrows():
        pattern = row['pattern']
        replacement = row['replacement']
        exp = re.compile(pattern)
        #Calculate digest for distringuishing patterns without ugly characters
        pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
        expressions[pattern_digest] = (exp, replacement)
    
    for content_block in root:
        cb_ix = content_block.attrib["ix"]
        page = content_block.attrib["page"]
        #content_txt = '\n'.join(content_block.itertext())
        for textblock in content_block:
            tb_ix = textblock.attrib["ix"]
            paragraph = textblock.text
            for pattern_digest, exp_tuple in expressions.items():
                exp, outpattern = exp_tuple
                for m in exp.finditer(paragraph):
                    matched_txt = m.group()
                    replacement = exp.sub(outpattern, matched_txt)
                    
                    d = {"protocol_id": protocol_id,
                    "pattern": pattern_digest,
                    "txt": matched_txt,
                    "replacement": replacement,
                    "page": int(page),
                    "cb_ix": int(cb_ix),
                    "tb_ix": int(tb_ix)}
                    data.append(d)
    
    columns = ["pattern", "txt", "replacement", "page", "cb_ix", "tb_ix"]
    return pd.DataFrame(data=data, columns=columns)

def apply_curations(protocol, instance_db):
    protocol_id = protocol.attrib["id"]
    applicable_instances = instance_db[instance_db["protocol_id"] == protocol_id]
    for _, row in applicable_instances.iterrows():
        cb_ix = row["cb_ix"]
        page = row["page"]
        for content_block in protocol.xpath("contentBlock[@ix='" + str(cb_ix) + "' and @page='" + str(page) + "' ]"):
            target = content_block
            tb_ix = row["tb_ix"]
            if not pd.isna(tb_ix):
                if len(content_block) > tb_ix:
                    target = content_block[tb_ix]
                else:
                    print("WARN: curation omitted p", page, "cb", cb_ix, "tb", tb_ix)
                    break
            
            txt = row["txt"]
            replacement = row["replacement"]
            paragraph = target.text
            paragraph = paragraph.replace(txt, replacement)
            target.text = paragraph
    
    if protocol_id == "prot-1960--fk--19":
        f = open("prot-1960--fk--19-curation.xml", "wb")
        b = etree.tostring(protocol, encoding="utf-8", pretty_print=True)
        f.write(b)
        f.close()
    return protocol

def curation_workflow(package_id, archive, pattern_db):
    package = archive.get(package_id)
    page_content_blocks = get_blocks(package, package_id)
    instance_db = find_instances(page_content_blocks, pattern_db)
    instance_db["protocol_id"] = package_id
    instance_db = instance_db.drop_duplicates()
    return instance_db
    
