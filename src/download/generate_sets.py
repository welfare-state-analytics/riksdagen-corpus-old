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

def get_sets(decade, interval=10, set_size=2):
    total = 2 * set_size    
    pages = pd.read_csv("db/protocols/pages.csv")

    pages_decade = pages[(pages["year"] >= decade) & (pages["year"] < decade + interval)]
    pages_decade = pages_decade.sort_values('ordinal')
    pages_decade = pages_decade.head(n=total)
    pages_decade = pages_decade.reset_index()

    print(pages_decade)

    infolder = "pdf/"
    outfolder = "data/curation/" + str(decade) + "-" + str(decade + interval-1) + "/"
    
    create_dirs(outfolder)

    for ix, row in pages_decade.iterrows():
        
        print(row)
        '''
        folder = "train/"
        if ix % 2 == 1:
            folder = "test/"

        folder = outfolder + folder
        ix = ix // 2

        filename = row["filename"]
        pagenumber = row["pagenumber"]
        print(ix, filename, pagenumber, folder)

        path = folder + str(ix) + "/"
        if not os.path.exists(path):
            print("Create folder", path)
            os.mkdir(path)

        info = open(path + "info.yaml", "w")

        info.write("filename: " + filename + "\n")
        info.write("pagenumber: " + str(pagenumber) + "\n")

        info.close()
        
        # Copy correct page from PDF to sample folder
        pdf_in = infolder + filename
        pdf_out = path + filename
        
        pdf_reader = PdfFileReader(open(pdf_in, 'rb'))
        pdf_writer = PdfFileWriter()
        
        pdf_writer.addPage(pdf_reader.getPage(pagenumber - 1))
    
        output = open(pdf_out,'wb')
        pdf_writer.write(output)
        
        output.close()
        
        original = open(path + "original.txt", "w")
        annotated = open(path + "annotated.txt", "w")
        
        original.close()
        annotated.close()
        '''
    
if __name__ == "__main__":
    set_size = 2
    get_sets(1970, set_size=set_size)

