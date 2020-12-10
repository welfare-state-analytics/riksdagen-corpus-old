import lxml
import xmlschema
import xml.etree.ElementTree as et
import sys, re
from bs4 import BeautifulSoup
import pandas as pd

def clean_html(raw_html):
    raw_html = raw_html.replace("\n", " NEWLINE ")
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace(" NEWLINE ", "\n")
    return cleantext

def read_xml(outpath):
    xml_path = sys.argv[1]
    xml = open(xml_path).read()
    s = clean_html(xml)

    print(s)

    f = open(xml_path)
    soup = BeautifulSoup(f)
    f.close()
    g = open(outpath, 'w')
    g.write(soup.prettify())
    g.close()

def validate_xml_schema(xml_path, schema_path):
    schema = xmlschema.XMLSchema(schema_path)
    return schema.is_valid(xml_path)

def validate_parla_clarin_example():
    xml_path = "data/xml/parla-clarin.xml"

    s = open(xml_path).read()[:50]
    print("Example Parla-clarin XML: '", s, " [...]'")
    schema_path = "schemas/parla-clarin.xsd"

    valid = validate_xml_schema(xml_path, schema_path)

    print("XML is valid", valid)
    
def update_db(updated_db, db_path, check_columns=True, remove=None, replace=None):
    old_db = pd.read_json(db_path, orient="records", lines=True)
    print("Old", old_db)
    print("Updates", updated_db)
    if check_columns:
        assert tuple(old_db.columns) == tuple(updated_db.columns)

    new_db = pd.concat([old_db, updated_db], sort=False)

    # TODO: Remove rows from the original dataframe


    # Replace duplicates based on the given column combinations
    if replace is not None:
        new_db = new_db.groupby(replace).last().reset_index()
    print("New", new_db)
    new_db.to_json(db_path, orient="records", lines=True)
    print("New on disk", pd.read_json(db_path, orient="records", lines=True))


def update_test():
    db_path = "test.json"

    d1 = {'name': ["A", "A", "C"], 'country': ["SWE", "FIN","FIN"], 'value': [3, 2, 4]}
    d2 = {'name': ["C", "C"], 'country': ["FIN", "GER"], 'value': [8,7]}

    df1 = pd.DataFrame(data=d1)
    df2 = pd.DataFrame(data=d2)
    df1.to_json(db_path, orient="records", lines=True)
    update_db(df2, db_path, replace=["name", "country"])

if __name__ == '__main__':
    #validate_parla_clarin_example()
    update_test()
