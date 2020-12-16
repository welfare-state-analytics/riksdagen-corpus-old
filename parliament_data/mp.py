"""
Handles the data on the members of parliament.
"""

import pandas as pd

def create_database():
    pass


def detect_mp(introduction, metadata, mp_db):
    """
    """

    year = metadata["year"]
    mp_db = mp_db[(mp_db["start"] <= year) & (mp_db["end"] >= year)]

    for ix, row in mp_db.iterrows():
        name = row["name"]
        last_name = " ".join(name.split()[1:])
        if last_name in introduction:
            return row


if __name__ == '__main__':
    
    columns = ["name", "constituency", "party", "start", "end"]
    row1 = ["Håkan Svensson", "Stockholm", "olego", 1970, 1970]
    row2 = ["Olof Palme", "Linköping", "olego", 1970, 1970]

    mp_db = pd.DataFrame([row1, row2], columns=columns)
    print(mp_db)

    introduction = "Anf. Palme yttrade:"

    metadata = dict(
        year=1970,
    )

    mp = detect_mp(introduction, metadata, mp_db)

    print("MP:", mp)

