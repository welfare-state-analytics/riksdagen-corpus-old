from kblab import Archive
import getpass
import numpy as np
import pandas as pd
import time
import hashlib
from parliament_data.download.count_pages import login_to_archive

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

if __name__ == '__main__':
    files = pd.read_csv("db/protocols/files.csv")
    randomized = randomize_ordinals(files)
    print(randomized)
    
    randomized.to_csv("db/protocols/pages.csv")
