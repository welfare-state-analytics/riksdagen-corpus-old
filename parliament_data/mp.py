"""
Handles the data on the members of parliament.
"""

import pandas as pd

def create_database(csv_path):

    df = pd.read_csv(csv_path)

    years = csv_path.split("/")[-1].split(".")[0].split("-")

    start = int(years[0])
    end = int(years[1])

    df["start"] = start
    df["end"] = end

    return df


def detect_mp(introduction, metadata, mp_db):
    """
    Detect which member of parliament is mentioned in a given introduction.

    Params:
        introuction: An introduction to a speech in the protocols. String.
        metadata: Year and chamber of the parliamentary proceeding in question. Dict.
        mp_db: MP database as a Pandas DataFrame.
    """

    year = metadata["year"]
    mp_db = mp_db[(mp_db["start"] <= year) & (mp_db["end"] >= year)]

    for ix, row in mp_db.iterrows():
        name = row["Riksdagsledamot"]
        last_name = " ".join(name.split()[1:])
        if last_name in introduction:
            return row


if __name__ == '__main__':

    mp_db = create_database("data/mp/1971-1973.csv")
    print(mp_db)

    introduction = "Anf. Palme yttrade:"

    metadata = dict(
        year=1972,
    )

    mp = detect_mp(introduction, metadata, mp_db)

    print("MP:", mp)
