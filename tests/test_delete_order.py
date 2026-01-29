
import unittest
import sqlite3
import os
from src.database import DatabaseManager

class TestDeleteOrder(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_delete.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_delete_order(self):
        # 1. Create order with items
        item = {"ad": "Test Prod", "adet": 1, "fiyat": 50.0}
        oid = self.db.create_order("Cust", "123", "Loc", [item])

        # Verify creation
        orders = self.db.get_orders("Pending")
        self.assertEqual(len(orders), 1)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM order_items WHERE order_id=?", (oid,))
        item_count = cursor.fetchone()[0]
        self.assertEqual(item_count, 1)
        conn.close()

        # 2. Delete order
        self.db.delete_order(oid)

        # 3. Verify deletion
        orders = self.db.get_orders("Pending")
        self.assertEqual(len(orders), 0)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM order_items WHERE order_id=?", (oid,))
        item_count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(item_count, 0) # Items should be gone

if __name__ == '__main__':
    unittest.main()
