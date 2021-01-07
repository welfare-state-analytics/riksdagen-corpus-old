"""
Handles the data on the members of parliament.
"""

import pandas as pd

def create_database(path):
    extension = path.split(".")[-1]

    if extension == "csv":
        df = pd.read_csv(path, skip_blank_lines=True)
        nulls = df.isnull().values.all(axis=0)
        nulls = zip(df.columns, nulls)
        
        for column_name, null in nulls:
            if null:
                del df[column_name]
        
        new_columns = list(df.columns)
        print(new_columns)
        for column_ix, column_name in enumerate(df.columns):
            if "." in column_name:
                new_name = column_name.split(".")[0]
                new_columns[column_ix] = new_name
        
        df.columns = new_columns
        
    elif extension == "txt":
        f = open(path)
        #columns = ["Ledamöt"]
        
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
                    row = [lan] + row
                    
                    rows.append(row)
                    
        for row in rows:
            print(row)
        df = None
        
        
    else:
        print("File type not supported.")
        return None
        
    years = path.split("/")[-1].split(".")[0].replace("–­­", "-").split("-")
    
    chamber = "enkammarsriksdagen"
    potential_chamber = path.split("/")[-2]
    if potential_chamber == "ak":
        chamber = "andra kammaren"
    elif potential_chamber == "fk":
        chamber = "första kammaren"
    
    df["chamber"] = chamber
    
    if len(years) == 2:
        start = int(years[0])
        end = int(years[1])
    elif len(years) == 1:
        df["start"] = int(years[0])
        df["end"] = int(years[0])
    
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
    '''
    mp_db = create_database("data/mp/1971-1973.csv")
    print(mp_db)

    introduction = "Anf. Palme yttrade:"

    metadata = dict(
        year=1972,
    )

    mp = detect_mp(introduction, metadata, mp_db)

    print("MP:", mp)
    '''
    
    #mp_db = create_database("data/mp/ak/1945-1948.txt")
    mp_db = create_database("data/mp/1971-1973.csv")
    
    print(mp_db)
    
