import unittest
import pandas as pd

class Test(unittest.TestCase):

    # Test that each column in the MP DB contains at least 95% valid values
    def test_mp_db(self):
        lower_limit = 0.95
        
        mp_db = pd.read_csv("db/mp/members_of_parliament.csv")

        total = len(mp_db)
        mp_db_columns = mp_db.columns

        for column in mp_db_columns:
            column_count = len(mp_db[mp_db[column].isnull()])
            valid_ratio = 1. - (column_count / total)
            print(column, valid_ratio)
            self.assertGreaterEqual(valid_ratio, lower_limit)

if __name__ == '__main__':
    unittest.main()
