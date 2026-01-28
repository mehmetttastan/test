import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager

class TestSystemFlow(unittest.TestCase):
    def setUp(self):
        # Use a test db
        self.test_db_name = "test_shop_v3.db"
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)
        self.db = DatabaseManager(self.test_db_name)

    def tearDown(self):
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

    def test_product_rename(self):
        p = self.db.get_products_by_category("Kahve")[0]
        new_name = "Updated Name"
        self.db.update_product(p['id'], new_name, p['price'], p['stock'], 1)
        
        p_new = self.db.get_products_by_category("Kahve")[0]
        self.assertEqual(p_new['name'], new_name)

    def test_expense_filtering(self):
        self.db.add_expense("Kahve", "Exp1", 10.0)
        self.db.add_expense("Kuru Meyve", "Exp2", 20.0)
        
        coffee_expenses = self.db.get_expenses("Kahve")
        self.assertEqual(len(coffee_expenses), 1)
        self.assertEqual(coffee_expenses[0]['description'], "Exp1")
        
        all_expenses = self.db.get_expenses()
        self.assertEqual(len(all_expenses), 2)

if __name__ == '__main__':
    unittest.main()
