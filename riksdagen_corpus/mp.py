"""
Handles the data on the members of parliament.
"""

import pandas as pd
import os

def create_database(path):
    extension = path.split(".")[-1]

    if extension == "csv":
        print("Read:", path)
        df = pd.read_csv(path, skip_blank_lines=True)

        # Drop columns where everything is null
        nulls = df.isnull().values.all(axis=0)
        nulls = zip(df.columns, nulls)
        for column_name, null in nulls:
            if null:
                del df[column_name]
        
        new_columns = list(df.columns)
        for column_ix, column_name in enumerate(df.columns):
            if "." in column_name:
                new_name = column_name.split(".")[0]
                new_columns[column_ix] = new_name
        
        df.columns = new_columns
        
    elif extension == "txt":
        print("Read:", path)
        f = open(path)
        columns = ["Riksdagsledamot", "Parti", "Valkrets"]
        
        rows = []
        lan = None
        for line in f:
            line = line.replace("\n", "")
            if len(line) > 2:
                indented = line[:4] == "    "
                
                # Non-indented lines are titles, which correspond to 'län' / region
                if not indented:
                    lan = line
                else:
                    row = line.split(",")
                    row = [x.strip() for x in row]
                    
                    datapoint = []
                    # Add name
                    datapoint.append(row[0])
                    # Add party
                    datapoint.append(row[-1])
                    # Add 'län' / region
                    datapoint.append(lan)
                    rows.append(datapoint)

        df = pd.DataFrame(rows, columns = columns)
    else:
        print("File type not supported.", path)
        return None
    
    # Harmonize name to be Riksdagsledamot
    new_columns = list(df.columns)
    for column_ix, column_name in enumerate(df.columns):
        if column_name in ["Ledamot", "Riksdagsledamot", "Namn"]:
            new_columns[column_ix] = "Riksdagsledamot"
    df.columns = new_columns
    
    # Drop unnecessary columns
    retain = ["Riksdagsledamot", "Parti", "Valkrets", "Yrke"]
    for column_name in df.columns:
        if column_name not in retain:
            del df[column_name]
    
    # Chamber
    chamber = "Enkammarriksdagen"
    potential_chamber = path.split("/")[-2]
    if potential_chamber == "ak":
        chamber = "Andra kammaren"
    elif potential_chamber == "fk":
        chamber = "Första kammaren"
    df["chamber"] = chamber
    
    # Year in office
    year_str = path.split("/")[-1].split(".")[0].replace("–­­", "-")
    if len(year_str) == 9:
        df["start"] = int(year_str[:4])
        df["end"] = int(year_str[-4:])
    elif len(year_str) == 4:
        df["start"] = int(year_str)
        df["end"] = int(year_str)
    
    return df

def create_full_database(dirs):
    mp_dbs = []
    for d in dirs:
        for path in os.listdir(d):
            full_path = os.path.join(d, path)
            mp_db = create_database(full_path)
            if mp_db is not None:
                mp_dbs.append(mp_db)
    mp_db = pd.concat(mp_dbs)
    
    mp_db = mp_db.sort_values(by=["start", "chamber", "Riksdagsledamot"], ignore_index=True)

    columnsTitles = ['Riksdagsledamot' , 'Parti', 'Valkrets', 'chamber', 'start', 'end', 'Yrke']
    mp_db = mp_db.reindex(columns=columnsTitles)

    mp_db = mp_db[mp_db["Riksdagsledamot"].notnull()]

    return mp_db

def add_gender(mp_db, names):
    mp_db["gender"] = None

    for i, row in mp_db.iterrows():
        first_name = row["Riksdagsledamot"].split()[0]
        for j, namerow in names[names["name"] == first_name].iterrows():
            mp_db.loc[i, 'gender'] = namerow["gender"]

    return mp_db


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
    
    mp_dbs = []
    dirs = ["data/mp/", "data/mp/fk/", "data/mp/ak/"]

    mp_dbs = create_full_database(dirs)
    print(mp_dbs)
    
    mp_dbs.to_csv("db/mp/1921-2022.csv")
