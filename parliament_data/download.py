import pandas as pd
import os
import shutil
from PyPDF2 import PdfFileReader, PdfFileWriter
from lxml import etree
import re
import getpass
import kblab

def login_to_archive():
    """
    Prompts the user for username and password, and logs in to KBLab. Returns the resulting KBLab client archive.
    """
    username = input("Username: ")
    password = getpass.getpass()
    print("Password set for user:", username)
    
    return kblab.Archive('https://betalab.kb.se', auth=(username, password))

def get_blocks(s):
    """
    Get content and text blocks from an OCR output XML file. Concatenate words into sentences.

    Args:
        s: OCRd XML as a string.

    Returns an lxml elem tree with the structure page > contentBlock > textBlock.
    """
    tree = etree.fromstring(s)

    ns_dict = {"space": "http://www.loc.gov/standards/alto/ns-v3#"}
    content_blocks = tree.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}ComposedBlock')

    page_e = etree.Element("page")
    
    for content_block in content_blocks:
        content_block_e = etree.SubElement(page_e, "contentBlock")
        text_blocks = content_block.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}TextBlock')
        for text_block in text_blocks:
            tblock = []
            text_lines = text_block.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}TextLine')
            
            for text_line in text_lines:
                strings = text_line.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}String')
                for string in strings:
                    content = string.attrib["CONTENT"]
                    tblock.append(content)
            
            tblock = " ".join(tblock)
            # Remove line breaks when next line starts with a small letter
            tblock = re.sub('([a-zåäö,])\n ?([a-zåäö])', '\\1 \\2', tblock)
            text_block_e = etree.SubElement(content_block_e, "textBlock")
            text_block_e.text = tblock
    
    return page_e


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

def _create_dirs(outfolder):
    if not os.path.exists(outfolder):
        print("Create folder", outfolder)
        os.mkdir(outfolder)

    if not os.path.exists(outfolder + "train/"):
        os.mkdir(outfolder + "train/")

    if not os.path.exists(outfolder + "test/"):
        os.mkdir(outfolder + "test/")

def fetch_files(package, extension="xml", return_files=False):
    """
    Fetch all files with the provided extension from a KBLab package

    Args:
        package: KBLab client package
        extension: File extension of the files that you want to fetch. String, or None which outputs all filetypes.
        return_files: Whether to return filenames or files zipped with filenames. Boolean, default value False returns just filenames.

    Depending on return_files, either outputs a list of filenames, or a list of file and filename tuples (String, String).
    """
    filelist = package.list()
    if extension is not None:
        filelist = [f for f in filelist if f.split(".")[-1] == extension]
    filelist = sorted(filelist)
    
    if not return_files:
        return filelist
    else:
        files = [package.get_raw(f).read() for f in filelist]
        return zip(files, filelist)

def generate_sets(decade, interval=10, set_size=2, txt_dir=None):
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
    _create_dirs(outfolder)
    
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
        package = archive.get(package_id)
        jp2list = fetch_files(package, extension="jp2")
        jp2numbers = [ int(f.split(".")[-2].split("-")[-1]) for f in jp2list]
        
        index = jp2numbers.index(pagenumber)        
        jp2file = jp2list[index]
        imagedata = package.get_raw(jp2file).read()
        
        jp2out = open(path + "image.jp2", "wb")
        jp2out.write(imagedata)
        jp2out.close()
        
        if txt_dir is not None:
            txt_filename = jp2file.split("-")[0] + ".txt"
            txt = open(txt_dir + txt_filename).read()
            
            txtout = open(path + txt_filename, "w")
            txtout.write(txt)
            txtout.close()

def _get_seed(string):
    encoded = string.encode('utf-8')
    digest = hashlib.md5(encoded).hexdigest()[:8]
    return int(digest, 16)

def randomize_ordinals(files):
    columns = ["package_id", "year", "pagenumber", "ordinal"]
    data = []
    for index, row in files.iterrows():
        #print(index, row)
        package_id = row["package_id"]
        pages = row["pages"]
        year = row["year"]

        for page in range(0, pages):

            seedstr = package_id + str(year) + str(page)
            np.random.seed(_get_seed(seedstr))
            ordinal = np.random.rand()
            new_row = [package_id, year, page, ordinal]
            data.append(new_row)

    return pd.DataFrame(data, columns = columns)


if __name__ == "__main__":
    set_size = 2
    txt_dir = "../riksdagens_protokoll/riksdagens_protokoll/"
    for decennium in range(1920, 1990, 10):
        generate_sets(decennium, set_size=set_size, txt_dir=txt_dir)

