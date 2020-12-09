import pandas as pd
import os
import shutil
from PyPDF2 import PdfFileReader, PdfFileWriter
from count_pages import login_to_archive

def create_dirs(outfolder):
    if not os.path.exists(outfolder):
        print("Create folder", outfolder)
        os.mkdir(outfolder)

    if not os.path.exists(outfolder + "train/"):
        os.mkdir(outfolder + "train/")

    if not os.path.exists(outfolder + "test/"):
        os.mkdir(outfolder + "test/")

def get_sets(decade, interval=10, set_size=2, txt_dir=None):
    # Read pages dataframe, filter relevant data and sort
    total = 2 * set_size
    pages = pd.read_csv("db/protocols/pages.csv")
    pages_decade = pages[(pages["year"] >= decade) & (pages["year"] < decade + interval)]
    pages_decade = pages_decade.sort_values('ordinal')
    pages_decade = pages_decade.head(n=total)
    pages_decade = pages_decade.reset_index()

    print(pages_decade)
    
    # Create folder for the decennium
    outfolder = "data/curation/" + str(decade) + "-" + str(decade + interval-1) + "/"
    create_dirs(outfolder)
    
    # Ask for credentials and establish connection 
    archive = login_to_archive()

    for ix, row in pages_decade.iterrows():
    
        package_id = row["package_id"]
        pagenumber = row["pagenumber"]
        print(ix, package_id, pagenumber)
        
        # Create folder for either train or test set
        folder = "train/"
        if ix % 2 == 1:
            folder = "test/"
        folder = outfolder + folder
        ix = ix // 2
    
        path = folder + str(ix) + "/"
        if not os.path.exists(path):
            print("Create folder", path)
            os.mkdir(path)
        
        # Write info.yaml
        info = open(path + "info.yaml", "w")
        info.write("package_id: " + package_id + "\n")
        info.write("pagenumber: " + str(pagenumber) + "\n")
        info.close()
        
        # Create empty original.txt and annotated.txt files
        original = open(path + "original.txt", "w")
        annotated = open(path + "annotated.txt", "w")
        original.close()
        annotated.close()
                
        # Download jp2 file and save it to disk
        str(pagenumber)
        package = archive.get(package_id)
        filelist = package.list()
        jp2list = [f for f in filelist if f.split(".")[-1] == "jp2"]
        jp2numbers = [ int(f.split(".")[-2].split("-")[-1]) for f in jp2list]
        
        index = jp2numbers.index(pagenumber)
        
        jp2file = jp2list[index]
        print(jp2file)
        
        imagedata = package.get_raw(jp2file).read()
        
        jp2out = open(path + "image.jp2", "wb")
        jp2out.write(imagedata)
        jp2out.close()
        #jp2file = archive.search()
        
        if txt_dir is not None:
            txt_filename = jp2file.split("-")[0] + ".txt"
            txt = open(txt_dir + txt_filename).read()
            
            txtout = open(path + txt_filename, "w")
            txtout.write(txt)
            txtout.close()
        
    
if __name__ == "__main__":
    set_size = 2
    txt_dir = "../riksdagens_protokoll/riksdagens_protokoll/"
    get_sets(1960, set_size=set_size, txt_dir=txt_dir)

