import unittest

import math
import os
from parliament_data.utils import validate_xml_schema

class Test(unittest.TestCase):

    # SGNS log probability. Batch size == 2
    def test_official_example(self):
        # Reads all files from datapath.
        schema_path = "schemas/parla-clarin.xsd"
        xml_path = "data/parla-clarin/official-example.xml"
        
        valid = validate_xml_schema(xml_path, schema_path)
        # Vocab is a bijection
        self.assertEqual(valid, True)


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
