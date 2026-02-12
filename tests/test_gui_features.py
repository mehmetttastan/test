
import unittest
import sqlite3
import os
from src.database import DatabaseManager

class TestGUIFeatures(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_gui_features.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_historical_order_flow(self):
        # 1. Create Historical Order
        self.db.create_historical_order("Ahmet", 100.0, "2023-01-01 12:00:00")

        orders = self.db.get_orders("Delivered")
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['customer_name'], "Ahmet")
        self.assertEqual(orders[0]['total_price'], 100.0)
        self.assertEqual(orders[0]['created_at'], "2023-01-01 12:00:00")

        # 2. Update Order
        oid = orders[0]['id']
        self.db.update_order_details(oid, "Mehmet", 150.0, "2023-01-02 12:00:00")

        updated_orders = self.db.get_orders("Delivered")
        self.assertEqual(updated_orders[0]['customer_name'], "Mehmet")
        self.assertEqual(updated_orders[0]['total_price'], 150.0)
        self.assertEqual(updated_orders[0]['created_at'], "2023-01-02 12:00:00")

    def test_product_report(self):
        # Create normal orders with items
        p1 = {"ad": "Kahve", "adet": 2, "fiyat": 100.0}
        p2 = {"ad": "Meyve", "adet": 1, "fiyat": 50.0}

        # Order 1: 2 Kahve
        self.db.create_order("Cust1", "123", "Loc", [p1])
        # Order 2: 1 Kahve, 1 Meyve
        self.db.create_order("Cust2", "123", "Loc", [p1, p2])

        # Mark all as delivered
        orders = self.db.get_orders("Pending")
        for o in orders:
            self.db.update_order_status(o['id'], "Delivered")

        # Check Report
        report = self.db.get_product_sales_report()
        # Should have Kahve (4 qty, 200 total) and Meyve (1 qty, 50 total)

        # Convert to dict for easier check
        report_dict = {row[0]: {'qty': row[1], 'rev': row[2]} for row in report}

        self.assertEqual(report_dict['Kahve']['qty'], 4)
        self.assertEqual(report_dict['Kahve']['rev'], 200.0)
        self.assertEqual(report_dict['Meyve']['qty'], 1)
        self.assertEqual(report_dict['Meyve']['rev'], 50.0)

if __name__ == '__main__':
    unittest.main()
