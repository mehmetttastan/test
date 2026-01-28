import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager

class TestSystemFlow(unittest.TestCase):
    def setUp(self):
        # Use a test db
        self.test_db_name = "test_shop_v2.db"
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)
        self.db = DatabaseManager(self.test_db_name)

    def tearDown(self):
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

    def test_mixed_order_and_income_split(self):
        # 1. User places mixed order
        coffee_products = self.db.get_products_by_category("Kahve")
        fruit_products = self.db.get_products_by_category("Kuru Meyve")
        
        p1 = coffee_products[0] # Coffee
        p2 = fruit_products[0] # Fruit
        
        cart = [
            {"id": p1['id'], "ad": p1['name'], "adet": 1, "fiyat": 250.0},
            {"id": p2['id'], "ad": p2['name'], "adet": 1, "fiyat": 50.0}
        ]
        
        order_id = self.db.create_order("Test User", "123", "Office", cart)
        
        # 2. Mark as Delivered
        self.db.update_order_status(order_id, "Delivered")
        
        # 3. Check separate incomes
        self.assertEqual(self.db.get_total_income("Kahve"), 250.0)
        self.assertEqual(self.db.get_total_income("Kuru Meyve"), 50.0)

    def test_separate_expenses(self):
        # Add categorized expenses
        self.db.add_expense("Kahve", "Kahve Çekirdeği", 100.0)
        self.db.add_expense("Kuru Meyve", "Meyve Alımı", 20.0)
        self.db.add_expense("Genel", "Elektrik", 50.0)
        
        # Check totals
        self.assertEqual(self.db.get_total_expenses("Kahve"), 100.0)
        self.assertEqual(self.db.get_total_expenses("Kuru Meyve"), 20.0)
        self.assertEqual(self.db.get_total_expenses("Genel"), 50.0)
        self.assertEqual(self.db.get_total_expenses(), 170.0)

    def test_stock_update(self):
        p = self.db.get_products_by_category("Kahve")[0]
        initial_stock = p['stock']
        
        # Order 1
        cart = [{"id": p['id'], "ad": p['name'], "adet": 1, "fiyat": 10.0}]
        self.db.create_order("U", "P", "D", cart)
        
        # Check stock reduced
        p_new = self.db.get_products_by_category("Kahve")[0]
        self.assertEqual(p_new['stock'], initial_stock - 1)

if __name__ == '__main__':
    unittest.main()
