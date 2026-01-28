import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager

class TestSystemFlow(unittest.TestCase):
    def setUp(self):
        # Use a test db
        self.test_db_name = "test_shop_v4.db"
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)
        self.db = DatabaseManager(self.test_db_name)

    def tearDown(self):
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

    def test_coupons(self):
        # 1. Create Coupon
        self.db.add_coupon("TEST10", 10, limit=2)
        
        c = self.db.get_coupon("TEST10")
        self.assertIsNotNone(c)
        self.assertEqual(c['discount_percent'], 10)
        
        # 2. Use Coupon in Order
        cart = [{"id": 1, "ad": "Prod", "adet": 1, "fiyat": 100.0}]
        # Discount 10% = 10 TL
        order_id = self.db.create_order("U", "P", "D", cart, coupon_code="TEST10", discount_amount=10.0)
        
        # 3. Check Coupon Usage
        c_updated = self.db.get_coupon("TEST10")
        self.assertEqual(c_updated['used_count'], 1)
        
        # 4. Check Order Total in DB
        orders = self.db.get_orders()
        o = orders[0]
        self.assertEqual(o['total_price'], 90.0) # 100 - 10
        self.assertEqual(o['coupon_code'], "TEST10")

    def test_charts_data(self):
        # Seed daily data
        # create_order uses CURRENT_TIMESTAMP, difficult to fake past dates easily without mocking time or direct SQL
        # We just test the method returns valid structure for today
        
        cart = [{"id": 1, "ad": "Prod", "adet": 1, "fiyat": 100.0}]
        order_id = self.db.create_order("U", "P", "D", cart)
        self.db.update_order_status(order_id, "Delivered")
        
        data = self.db.get_daily_income()
        self.assertEqual(len(data), 1) # Today
        self.assertEqual(data[0][1], 100.0)

if __name__ == '__main__':
    unittest.main()
