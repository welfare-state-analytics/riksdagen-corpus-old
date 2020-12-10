import lxml
import xmlschema

def validate(xml_path, schema_path):
    schema = xmlschema.XMLSchema(schema_path)
    return schema.is_valid(xml_path)

if __name__ == '__main__':
    xml_path = "data/xml/parla-clarin.xml"

    s = open(xml_path).read()[:50]
    print("XML:", s, " [...]")
    schema_path = "schemas/parla-clarin.xsd"

    valid = validate(xml_path, schema_path)

    print("XML is valid", valid)