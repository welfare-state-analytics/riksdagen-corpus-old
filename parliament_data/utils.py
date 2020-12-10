import lxml
import xmlschema
import xml.etree.ElementTree as et
import sys, re
from bs4 import BeautifulSoup

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

if __name__ == '__main__':
    validate_parla_clarin_example()
