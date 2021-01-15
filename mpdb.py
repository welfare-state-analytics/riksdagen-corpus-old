from riksdagen_corpus.mp import create_full_database
from riksdagen_corpus.mp import add_gender

dirs = ["data/mp/", "data/mp/fk/", "data/mp/ak/"]
mp_dbs = create_full_database(dirs)
print(mp_dbs)

mp_dbs.to_csv("db/mp/1921-2022.csv")