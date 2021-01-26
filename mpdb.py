import pandas as pd
from riksdagen_corpus.mp import create_full_database
from riksdagen_corpus.mp import add_gender, add_id
from riksdagen_corpus.mp import replace_party_abbreviations

dirs = ["data/mp/", "data/mp/fk/", "data/mp/ak/"]
mp_db = create_full_database(dirs)
print(mp_db)

names = pd.read_csv("db/mp/metadata/names.csv")
mp_db = add_gender(mp_db, names)
print(mp_db)

party_db = pd.read_csv("db/mp/parties.csv")
mp_db = replace_party_abbreviations(mp_db, party_db)

print(mp_db)

mp_db = add_id(mp_db)

print(mp_db)
mp_db.to_csv("db/mp/members_of_parliament.csv")
