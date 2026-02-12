
import unittest
import sqlite3
import os
from src.database import DatabaseManager

class TestGeneralExpenses(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_gen_exp.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_general_expense_retrieval(self):
        # 1. Add "Genel" expense
        self.db.add_expense("Genel", "Cleaning", 150.0)

        # 2. Retrieve via "Genel" filter
        expenses = self.db.get_expenses("Genel")
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0]['description'], "Cleaning")
        self.assertEqual(expenses[0]['amount'], 150.0)

        # 3. Check Totals
        total_gen = self.db.get_total_expenses("Genel")
        self.assertEqual(total_gen, 150.0)

if __name__ == '__main__':
    unittest.main()
