from riksdagen_corpus.mp import create_full_database
from riksdagen_corpus.mp import add_gender

dirs = ["data/mp/", "data/mp/fk/", "data/mp/ak/"]
mp_db = create_full_database(dirs)
print(mp_db)

mp_db.to_csv("db/mp/members_of_parliament.csv")
