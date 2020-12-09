from kblab import Archive
import getpass
import numpy as np
import pandas as pd
import time
import hashlib
from count_pages import login_to_archive

def get_seed(string):
	encoded = string.encode('utf-8')
	digest = hashlib.md5(encoded).hexdigest()[:8]
	return int(digest, 16)

columns = ["package_id", "year", "pagenumber", "ordinal"]

files = pd.read_csv("db/protocols/files.csv")

print(files)

data = []
for index, row in files.iterrows():
	#print(index, row)
	package_id = row["package_id"]
	pages = row["pages"]
	year = row["year"]

	for page in range(0, pages):

		seedstr = package_id + str(year) + str(page)
		np.random.seed(get_seed(seedstr))
		ordinal = np.random.rand()
		new_row = [package_id, year, page, ordinal]
		data.append(new_row)

randomized = pd.DataFrame(data, columns = columns)

print(randomized)

randomized.to_csv("db/protocols/pages.csv")
