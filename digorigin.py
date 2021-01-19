import os
from lxml import etree
import progressbar
import pandas as pd

from riksdagen_corpus.download import get_html_blocks
from riksdagen_corpus.utils import infer_metadata

dataraw = "data/raw/"
outfolder = "data/protocols/"
folders = os.listdir(dataraw)
folders = [dataraw + folder for folder in folders if os.path.isdir(dataraw + folder)]


print(folders)

columns = ["protocol_id", "year", "pages", "number"]
rows = []

for folder in sorted(folders):
    files = sorted(os.listdir(folder))

    print(folder)
    
    for fpath in progressbar.progressbar(files):
        root = get_html_blocks(folder + "/" + fpath)
        if root is not None:
            protocol_id = root.attrib["id"]
            metadata = infer_metadata(protocol_id)
            
            root_str = etree.tostring(root, encoding="utf-8", pretty_print=True).decode("utf-8")
            
            if not os.path.exists(outfolder + protocol_id):
                os.mkdir(outfolder + protocol_id)
                
            f = open(outfolder + protocol_id + "/original.xml", "w")
            f.write(root_str)
            f.close()
            
            row = [protocol_id, metadata["year"], None, metadata["number"]]
            
            # Set pages to 1 if there is content
            if len("".join(root.itertext())) >= 10:
                 row[2] = 1
            
            rows.append(row)


protocol_db = pd.DataFrame(rows, columns=columns)
print(protocol_db)

protocol_db.to_csv("db/protocols/digital_originals.csv")
