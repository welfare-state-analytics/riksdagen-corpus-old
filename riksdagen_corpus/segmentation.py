"""
Implements the segmentation of the data into speeches and
ultimately into the Parla-Clarin XML format.
"""

import pandas as pd
import re
import hashlib
import copy
import progressbar
from os import listdir
from os.path import isfile, join
from lxml import etree
from riksdagen_corpus.mp import detect_mp
from riksdagen_corpus.download import get_blocks, fetch_files, login_to_archive
from riksdagen_corpus.utils import infer_metadata

def _is_metadata_block(txt0):
    txt1 = re.sub("[^a-zA-ZåäöÅÄÖ ]+", "", txt0)
    len0 = len(txt0)
    
    # Empty blocks should not be classified as metadata
    if len(txt0.strip()) == 0:
        return False
        
    # Metadata generally don't introduce other things
    if txt0.strip()[-1] == ":":
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

def _detect_mp(matched_txt, names_ids):
    person = None
    for name, identifier in names_ids:
        if name in matched_txt:
            person = identifier
    
    if person == None:
        for name, identifier in names_ids:
            if name.upper() in matched_txt:
                person = identifier
    
    # Only match last name if full name is not found
    if person == None:
        for name, identifier in names_ids:
            last_name = " " + name.split()[-1]
            if last_name in matched_txt:
                person = identifier
            elif last_name.upper() in matched_txt:
                person = identifier
    return person
    
# Instance detection
def find_instances_xml(root, pattern_db, mp_db=None):
    """
    Find instances of segment start and end patterns in a txt file.

    Args:
        root: root of an lxml tree to be pattern matched.
        pattern_db: Patterns to be matched as a Pandas DataFrame.
    """
    columns = ['protocol_id', "page", "cb_ix", "tb_ix", "pattern", "segmentation", "who", "id"]
    data = []
    protocol_id = root.attrib["id"]
    metadata = infer_metadata(protocol_id)
    pattern_rows = list(pattern_db.iterrows())
    
    mp_db = mp_db[mp_db["chamber"] == metadata["chamber"]]
    names = mp_db["name"]
    ids = mp_db["id"]
    names_ids = list(zip(names,ids))
    
    expressions = dict()
    for _, row in pattern_db.iterrows():
        pattern = row['pattern']
        exp = re.compile(pattern)
        #Calculate digest for distringuishing patterns without ugly characters
        pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
        expressions[pattern_digest] = exp
    
    prot_speeches = dict()
    for content_block in root:
        cb_ix = content_block.attrib["ix"]
        page = content_block.attrib.get("page", 0)
        content_txt = '\n'.join(content_block.itertext())
        if not _is_metadata_block(content_txt):
            for textblock in content_block:
                tb_ix = textblock.attrib["ix"]
                paragraph = textblock.text
                if type(paragraph) != str:
                    paragraph = ""
                
                for pattern_digest, exp in expressions.items():
                    for m in exp.finditer(paragraph):
                        matched_txt = m.group()
                        person = _detect_mp(matched_txt, names_ids)
                        d = {
                        "protocol_id": protocol_id,
                        "pattern": pattern_digest,
                        "who": person,
                        "segmentation": "speech_start",
                        "page": int(page),
                        "cb_ix": int(cb_ix),
                        "tb_ix": int(tb_ix)
                        }

                        speech_id = protocol_id + "-"
                        if person is None:
                            person = "unk"
                        prot_speeches[person] = prot_speeches.get(person, 0) + 1
                        speech_id += person + "-"
                        speech_id += "-" + str(prot_speeches[person])
                        d["id"] = speech_id
                        data.append(d)

                        break
        else:
            d = {"protocol_id": protocol_id, "pattern": None, "who": None, "segmentation": "metadata"}
            d["cb_ix"] = int(cb_ix)
            d["tb_ix"] = -1
            d["page"] = int(page)
            data.append(d)

    return pd.DataFrame(data, columns=columns)

def apply_instances(protocol, instance_db):
    protocol_id = protocol.attrib["id"]
    
    applicable_instances = instance_db[instance_db["protocol_id"] == protocol_id]
    for _, row in applicable_instances.iterrows():
        cb_ix = row["cb_ix"]
        page = row["page"]
        for content_block in protocol.xpath("contentBlock[@ix='" + str(cb_ix) + "' and @page='" + str(page) + "' ]"):
            target = content_block
            if row["tb_ix"] >= 0:
                target = content_block[row["tb_ix"]]
            
            target.attrib["segmentation"] = row["segmentation"]
            if type(row["who"]) == str:
                target.attrib["who"] = row["who"]
                if protocol_id == "prot-201314--22":
                    print(target)
                    print(target.attrib["who"])

            if type(row["id"]) == str:
                target.attrib["id"] = row["id"]
    
    if protocol_id == "prot-199293--10":
        f = open("prot-199293--10.xml", "wb")
        b = etree.tostring(protocol, encoding="utf-8", pretty_print=True)
        f.write(b)
        f.close()
    return protocol
    
def find_instances(protocol_id, archive, pattern_db, mp_db):
    page_content_blocks = get_blocks(protocol_id, archive)
    instance_db = find_instances_xml(page_content_blocks, pattern_db, mp_db=mp_db)
    
    instance_db["protocol_id"] = protocol_id
    return instance_db
    
