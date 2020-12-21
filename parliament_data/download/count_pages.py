from kblab import Archive
import getpass
import numpy as np
import pandas as pd
import time
from lxml import etree

def login_to_archive():
    username = input("Username: ")
    password = getpass.getpass()
    print("Password set for user:", username)
    
    return Archive('https://betalab.kb.se', auth=(username, password))

def get_blocks(s):
    """
    Get content and text blocks from an OCR output XML file.

    Params:
        s: OCRd XML as a string.

    Returns a list of lists, outer list of content blocks, which contain lists of text blocks.
    """
    tree = etree.fromstring(s)

    ns_dict = {"space": "http://www.loc.gov/standards/alto/ns-v3#"}
    content_blocks = tree.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}ComposedBlock')

    d = []
    
    for content_block in content_blocks:
        text_blocks = content_block.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}TextBlock')        
        cblock = []
        for text_block in text_blocks:
            tblock = []
            text_lines = text_block.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}TextLine')
            
            for text_line in text_lines:
                strings = text_line.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}String')
                for string in strings:
                    content = string.attrib["CONTENT"]
                    tblock.append(content)
                    
            tblock = " ".join(tblock)
            cblock.append(tblock)
                
        d.append(cblock)
                
    return d


def count_pages(start, end):
    years = range(start, end)
    archive = login_to_archive()
    
    rows = []
    
    now = time.time()
    diffs = []
    for year in years:
        params = { 'tags': 'protokoll', 'meta.created': str(year)}
        package_ids = archive.search(params, max=200)
        
        for package_id in package_ids:
            #print("Id:", package_id)
            
            package = archive.get(package_id)
            filelist = package.list()
            
            jp2list = [f for f in filelist if f.split(".")[-1] == "jp2"]
            page_count = len(jp2list)
            #print("Length of jp2 file list", page_count)
            
            rows.append([package_id, year, page_count])
            
        then = now
        now = time.time()
        diffs.append(now - then)
        
        avg_diff = np.mean(diffs[-5:])
        
        print("Year", year, "; avg time", avg_diff, "; to go", avg_diff * (end-year - 1) )
            
    columns = ["package_id", "year", "pages"]
    db_pages = pd.DataFrame(rows, columns=columns)
    return db_pages
    
if __name__ == "__main__":
    db_pages = count_pages(1920,1990)
    
    print(db_pages)
    
    db_pages.to_csv("db/protocols/pages.csv")

