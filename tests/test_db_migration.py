
import unittest
import sqlite3
import os
from src.database import DatabaseManager

class TestDBMigration(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_migration.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_migration_adds_columns(self):
        # 1. Create an "old" database manually
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Old schema WITHOUT coupon_code/discount_amount
        cursor.execute('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                phone TEXT,
                delivery_method TEXT,
                total_price REAL,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note TEXT
            )
        ''')
        # Create other tables required by DatabaseManager.__init__ to avoid unrelated errors
        cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, category_id INT, name TEXT, price REAL, stock INT, is_active BOOL)")
        # ... others are less critical for this specific test but let's be safe if init_db checks them

        conn.commit()
        conn.close()

        # 2. Initialize DatabaseManager (should trigger migration)
        db = DatabaseManager(self.test_db)

        # 3. Verify columns exist
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(orders)")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]

        self.assertIn("coupon_code", column_names)
        self.assertIn("discount_amount", column_names)

        conn.close()

if __name__ == '__main__':
    unittest.main()
