import os
from riksdagen_corpus.download import get_html_blocks
from lxml import etree
import progressbar

dataraw = "data/raw/"
outfolder = "data/protocols/"
folders = os.listdir(dataraw)
folders = [dataraw + folder for folder in folders if os.path.isdir(dataraw + folder)]

print(folders)

for folder in folders:
    files = sorted(os.listdir(folder))
    if folder == dataraw + "1990-1997":
        print(folder)
        
        for fpath in progressbar.progressbar(files):
            root = get_html_blocks(folder + "/" + fpath)
            if root is not None:
                protocol_id = root.attrib["id"]
                
                root_str = etree.tostring(root, encoding="utf-8", pretty_print=True).decode("utf-8")
                
                if not os.path.exists(outfolder + protocol_id):
                    os.mkdir(outfolder + protocol_id)
                    
                f = open(outfolder + protocol_id + "/original.xml", "w")
                f.write(root_str)
                f.close()
                    
                
            else:
                pass
                #print(fpath)

