"""
Provides functions for the curation of the parliamentary data.
"""

import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from riksdagen_corpus.download import get_blocks, fetch_files, login_to_archive
import hashlib

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
    
    for row in pattern_db.iterrows():
        row = row[1]
        pattern = row['pattern']
        
        exp = re.compile(pattern)
        
        for content_block in root.findall(".//contentBlock"):
            content_txt = '\n\n'.join(content_block.itertext())
            content_hash = hashlib.md5(content_txt.encode("utf-8")).hexdigest()
            
            # Perform other curations
            for textBlock in content_block:
                paragraph = textBlock.text
                for m in exp.finditer(paragraph):
                
                    matched_txt = m.group()
                    replacement = exp.sub(row['replacement'], matched_txt)
                    
                    # Calculate digest for distringuishing patterns without ugly characters
                    pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
                    d = {"pattern": pattern_digest, "txt": matched_txt, "replacement": replacement }
                    data.append(d)
                
    return pd.DataFrame(data=data, columns=["pattern", "txt", "replacement"])

def apply_curations(root, instance_db):
    instances = list(instance_db.iterrows())
    digest = hashlib.sha256(pd.util.hash_pandas_object(instance_db, index=True).values).hexdigest()
    
    root.attrib['curation'] = digest[:16]
    for textBlock in root.findall(".//textBlock"):
        paragraph = textBlock.text
        
        for ix, row in instances:
            txt = row["txt"]
            if txt in paragraph:
                replacement = row["replacement"]
                if type(replacement) != str:
                    replacement = ""
                paragraph = paragraph.replace(txt, replacement)
        
        textBlock.text = paragraph
    return root
    
def get_curated_blocks(package, package_id, instance_db):
    instance_db = instance_db[instance_db["protocol_id"] == package_id]
    blocks = get_blocks(package, package_id)
    blocks = apply_curations(blocks, instance_db)
    return blocks
    
def curation_workflow(package_id, archive, pattern_db):
    package = archive.get(package_id)
    page_content_blocks = get_blocks(package, package_id)
    instance_db = find_instances(page_content_blocks, pattern_db)
    instance_db["protocol_id"] = package_id
    instance_db = instance_db.drop_duplicates()
    return instance_db
    
