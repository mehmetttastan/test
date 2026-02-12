
import unittest
import sqlite3
import os
from src.database import DatabaseManager

class TestManualTotals(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_manual_totals.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_manual_order_appears_in_totals(self):
        # 1. Create Manual Order for "Kahve"
        self.db.create_historical_order("Ahmet", 100.0, "2023-01-01 12:00:00", "Kahve")

        # 2. Check Total Income
        kahve_inc = self.db.get_total_income("Kahve")
        self.assertEqual(kahve_inc, 100.0)

        fruit_inc = self.db.get_total_income("Kuru Meyve")
        self.assertEqual(fruit_inc, 0.0)

    def test_manual_expense_appears_in_totals(self):
        # 1. Create Expense for "Kuru Meyve"
        self.db.add_expense("Kuru Meyve", "Fruit Stock", 50.0)

        # 2. Check Total Expenses
        fruit_exp = self.db.get_total_expenses("Kuru Meyve")
        self.assertEqual(fruit_exp, 50.0)

        kahve_exp = self.db.get_total_expenses("Kahve")
        self.assertEqual(kahve_exp, 0.0)

if __name__ == '__main__':
    unittest.main()
