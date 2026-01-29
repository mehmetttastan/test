
import unittest
import sqlite3
import os
from src.database import DatabaseManager

class TestExpenseManagement(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_expense.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_delete_expense(self):
        # 1. Add Expense
        self.db.add_expense("Kahve", "Test Expense", 50.0)

        expenses = self.db.get_expenses("Kahve")
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0]['amount'], 50.0)
        exp_id = expenses[0]['id']

        # 2. Delete Expense
        self.db.delete_expense(exp_id)

        expenses_after = self.db.get_expenses("Kahve")
        self.assertEqual(len(expenses_after), 0)

if __name__ == '__main__':
    unittest.main()
