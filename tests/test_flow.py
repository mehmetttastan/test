import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager

class TestSystemFlow(unittest.TestCase):
    def setUp(self):
        # Use a test db
        self.test_db_name = "test_shop.db"
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)
        self.db = DatabaseManager(self.test_db_name)

    def tearDown(self):
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

    def test_product_seeding(self):
        coffee = self.db.get_products_by_category("Kahve")
        self.assertTrue(len(coffee) > 0)
        self.assertEqual(coffee[0]['category_name'], "Kahve")

    def test_order_flow(self):
        # 1. User (Bot) places order
        # Need to know IDs or names. Seeding sets names.
        # "Filtre Kahve (250 gr)", "Elma Cipsi (50 gr)"
        # Fetch actual IDs to be safe
        coffee_products = self.db.get_products_by_category("Kahve")
        fruit_products = self.db.get_products_by_category("Kuru Meyve")
        
        p1 = coffee_products[0] # Coffee
        p2 = fruit_products[0] # Fruit
        
        cart = [
            {"id": p1['id'], "ad": p1['name'], "adet": 2, "fiyat": 500.0},
            {"id": p2['id'], "ad": p2['name'], "adet": 1, "fiyat": 50.0}
        ]
        order_id = self.db.create_order("Ahmet Yilmaz", "5551234567", "Maltepe", cart, "Test Note")
        
        # 2. Admin (GUI) sees order
        orders = self.db.get_orders("Pending")
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['id'], order_id)
        self.assertEqual(orders[0]['total_price'], 550.0)
        
        # 3. Admin updates status to Delivered to count for income
        self.db.update_order_status(order_id, "Delivered")
        
        # 4. Check income split
        # Coffee income: 500, Fruit income: 50
        coffee_inc = self.db.get_total_income("Kahve")
        fruit_inc = self.db.get_total_income("Kuru Meyve")
        total_inc = self.db.get_total_income()
        
        self.assertEqual(coffee_inc, 500.0)
        self.assertEqual(fruit_inc, 50.0)
        # Note: get_total_income() without arg sums order totals. 
        # get_total_income(cat) sums item totals. 
        # They should match if no items are missing categories.
        self.assertEqual(coffee_inc + fruit_inc, 550.0) 
        self.assertEqual(total_inc, 550.0)

    def test_expenses(self):
        self.db.add_expense("Kira", 1000.0)
        self.db.add_expense("Elektrik", 200.0)
        
        total = self.db.get_total_expenses()
        self.assertEqual(total, 1200.0)

    def test_add_product(self):
        self.db.add_product("Kahve", "Yeni Kahve", 150.0, 10)
        prods = self.db.get_products_by_category("Kahve")
        names = [p['name'] for p in prods]
        self.assertIn("Yeni Kahve", names)

if __name__ == '__main__':
    unittest.main()
