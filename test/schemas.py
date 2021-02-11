import unittest

import pandas as pd
from lxml import etree
from riksdagen_corpus.utils import validate_xml_schema, infer_metadata
from riksdagen_corpus.download import get_blocks
from riksdagen_corpus.export import create_tei, create_parlaclarin
from riksdagen_corpus.segmentation import find_instances, apply_instances
from riksdagen_corpus.db import load_patterns

class Test(unittest.TestCase):

    # Official example parla-clarin 
    def test_official_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        parlaclarin_path = "data/parla-clarin/official-example.xml"
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)

    # Official example parla-clarin 
    def test_protocol(self):
        schema_path = "schemas/protocol.xsd"
        protocol_path = "data/protocols/prot-198990--93/original.xml"
        
        valid = validate_xml_schema(protocol_path, schema_path)
        self.assertEqual(valid, True)

    # Parla-clarin generated from example OCR XML
    def test_generated_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        protocol_id = "prot-198990--93"
        fname = "prot_198990__93-031.xml"
        
        # Package argument can be None since the file is already saved on disk
        content_blocks = get_blocks(protocol_id, None)
        metadata = infer_metadata(fname.split(".")[0])

        mp_db = pd.read_csv("db/mp/members_of_parliament.csv")
        segmentation_patterns = load_patterns(phase="segmentation")
        segmentation_db = find_instances(protocol_id, None, segmentation_patterns, mp_db)
        protocol = apply_instances(content_blocks, segmentation_db)
        tei = create_tei(protocol, metadata)
        parla_clarin_str = create_parlaclarin(tei, metadata)
        
        parlaclarin_path = "data/parla-clarin/generated-example.xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
