"""
Provides functions for the curation of the parliamentary data.
"""

import pandas as pd
import re
from os import listdir
from os.path import isfile, join
from parliament_data.download import get_blocks, fetch_files, login_to_archive
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

def find_instances(root, pattern_db):
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
        replace_directly = row['replace_directly']
        
        #print("PATTERN:", pattern)
        exp = re.compile(pattern)
        
        for content_block in root.findall(".//contentBlock"):
            content_txt = '\n'.join(content_block.itertext())
            
            if not replace_directly:
                for m in exp.finditer(content_txt):
                    matched_txt = m.group()
                    replacement = exp.sub(row['replacement'], matched_txt)
                    
                    # Calculate digest for distringuishing patterns without ugly characters
                    pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
                    d = {"pattern": pattern_digest, "txt": matched_txt, "replacement": replacement }
                    data.append(d)
                    
    return pd.DataFrame(data=data, columns=["pattern", "txt", "replacement"])

def get_curated_blocks():
    pass
    
def curation_workflow(package_id, archive, pattern_db):
    print("Curating package", package_id)
    package = archive.get(package_id)
    
    xml_files = fetch_files(package)
    instance_dbs = []

    for filename in xml_files:
        page_content_blocks = get_blocks(filename, package, package_id)
        instance_db = find_instances(page_content_blocks, pattern_db)
        instance_dbs.append(instance_db)
    
    instance_db = pd.concat(instance_dbs)
    instance_db["filename"] = package_id
    return instance_db
    
