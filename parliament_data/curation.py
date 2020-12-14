import pandas as pd
import re
from os import listdir
from os.path import isfile, join

def _langmod_loss(sentence):
    return 0.0

def improvement(sentence, regexp):
    """
    Calculates the improvement in probability for a suggested text edit. Returns a tuple of losses.
    """
    sentence_suggestion = regexp
    loss0 = _langmod_loss(sentence)
    loss1 = _langmod_loss(sentence_suggestion)

    return loss0, loss1

def find_instances(pattern_db, folder):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """
    instance_db = pd.DataFrame(columns = ['pattern', 'loc', 'txt']) 
    files = [folder + f for f in listdir(folder) if isfile(join(folder, f))]

    for filename in files:
        txt = open(filename).read()

        for row in pattern_db.iterrows():
            row = row[1]
            pattern = row['pattern']

            print("PATTERN:", pattern)
            exp = re.compile(pattern)
            print("EXP", exp)
            log_fname = filename.split("/")[-1]
            for m in exp.finditer(txt):
                d = {"filename": log_fname, "pattern": pattern, "loc": m.start(), "txt":m.group()}
                instance_db = instance_db.append(d, ignore_index=True)

    return instance_db

if __name__ == '__main__':
    pattern_path = "./db/curation/patterns.json"
    pattern_db = pd.read_json(pattern_path, orient="records", lines=True)
    folder = "./data/txt/"

    instance_db = find_instances(pattern_db, folder)
    print(instance_db)

    instances_path = "./db/curation/instances.json"
    instance_db.to_json(instances_path, orient="records", lines=True)
