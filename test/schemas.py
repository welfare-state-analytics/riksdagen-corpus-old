import unittest

from lxml import etree
from parliament_data.utils import validate_xml_schema
from parliament_data.download import get_blocks
from parliament_data.segmentation import create_tei, create_parlaclarin, infer_metadata

class Test(unittest.TestCase):

    # Official example parla-clarin 
    def test_official_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        parlaclarin_path = "data/parla-clarin/official-example.xml"
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)

    # Parla-clarin generated from example OCR XML
    def test_generated_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        xml_path = "data/xml/prot_198990__93-031.xml"
        
        xml_f = open(xml_path)
        content_blocks = get_blocks(xml_f.read())
        xml_f.close()
        metadata = infer_metadata(xml_path)
        
        tei = create_tei(content_blocks, metadata)
        parla_clarin = create_parlaclarin(tei, metadata)
        parla_clarin_str = etree.tostring(parla_clarin, pretty_print=True, encoding="utf-8", xml_declaration=True).decode("utf-8")
        
        parlaclarin_path = "data/parla-clarin/generated-example.xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
