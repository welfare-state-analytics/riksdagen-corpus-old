from kblab import Archive
import getpass
import numpy as np
import pandas as pd
import time

def login_to_archive():
    username = input("Username: ")
    password = getpass.getpass()
    print("Password set for user:", username)
    
    return Archive('https://betalab.kb.se', auth=(username, password))
    
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

