import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_NAME = "shop.db"

class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Products
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                price REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        ''')
        
        # Orders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                phone TEXT,
                delivery_method TEXT,
                total_price REAL,
                status TEXT DEFAULT 'Pending', -- Pending, Paid, Delivered, Cancelled
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note TEXT,
                coupon_code TEXT,
                discount_amount REAL DEFAULT 0
            )
        ''')
        
        # Order Items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_name TEXT,
                category_name TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
        ''')

        # Expenses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT,
                description TEXT,
                amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Coupons
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                code TEXT PRIMARY KEY,
                discount_percent INTEGER,
                usage_limit INTEGER DEFAULT 0, -- 0 means unlimited
                used_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # Settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # --- MIGRATIONS ---
        # Ensure 'coupon_code' and 'discount_amount' exist in 'orders' (for old DBs)
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN coupon_code TEXT")
        except sqlite3.OperationalError:
            pass # Column likely exists

        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN discount_amount REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass # Column likely exists

        conn.commit()
        self._seed_data(cursor)
        conn.commit()
        conn.close()

    def _seed_data(self, cursor):
        # Check if categories exist
        cursor.execute("SELECT count(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO categories (name) VALUES ('Kahve')")
            cursor.execute("INSERT INTO categories (name) VALUES ('Kuru Meyve')")
            
            # Get IDs
            cursor.execute("SELECT id FROM categories WHERE name='Kahve'")
            coffee_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT id FROM categories WHERE name='Kuru Meyve'")
            fruit_id = cursor.fetchone()[0]
            
            # Seed Products
            coffee_products = [
                ("Filtre Kahve (250 gr)", 250.0, 50),
                ("Çekirdek Kahve (250 gr)", 250.0, 50)
            ]
            fruit_products = [
                ("Elma Cipsi (50 gr)", 50.0, 100),
                ("Portakal Dilimleri (50 gr)", 60.0, 100),
                ("Çıtır Muz Dilimleri (50 gr)", 70.0, 100),
                ("Kivi Kurusu (50 gr)", 80.0, 100),
                ("Ananas Halkaları (50 gr)", 90.0, 100)
            ]
            
            for name, price, stock in coffee_products:
                cursor.execute("INSERT INTO products (category_id, name, price, stock, is_active) VALUES (?, ?, ?, ?, 1)", 
                               (coffee_id, name, price, stock))
                               
            for name, price, stock in fruit_products:
                cursor.execute("INSERT INTO products (category_id, name, price, stock, is_active) VALUES (?, ?, ?, ?, 1)", 
                               (fruit_id, name, price, stock))
            
            # Seed Settings
            default_iban_msg = (
                "👤 **Ad Soyad:** [FİLTRESSO]\n"
                "🏦 **Banka:** [T.C. İŞ BANKASI]\n"
                "🆔 `TR00 0000 0000 0000 0000 0000 00`"
            )
            welcome_msg = (
                "⚠️ **BİLGİLENDİRME** ⚠️\n"
                "Siparişlerinizi buradan oluşturabilirsiniz."
            )
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("iban_message", default_iban_msg))
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("welcome_message", welcome_msg))
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("admin_id", "123456789"))

    # --- Product Methods ---
    def get_products_by_category(self, category_name: str) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, c.name as category_name 
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            WHERE c.name = ? AND p.is_active = 1
        ''', (category_name,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_products(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, c.name as category_name 
            FROM products p 
            JOIN categories c ON p.category_id = c.id
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_product(self, product_id, name, price, stock, is_active):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products SET name=?, price=?, stock=?, is_active=? WHERE id=?
        ''', (name, price, stock, is_active, product_id))
        conn.commit()
        conn.close()

    def add_product(self, category_name, name, price, stock):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name=?", (category_name,))
        cat_res = cursor.fetchone()
        if not cat_res:
            return False
        cat_id = cat_res[0]
        cursor.execute('''
            INSERT INTO products (category_id, name, price, stock, is_active) VALUES (?, ?, ?, ?, 1)
        ''', (cat_id, name, price, stock))
        conn.commit()
        conn.close()
        return True

    # --- Order Methods ---
    def create_order(self, customer_name, phone, delivery_method, cart_items, note="", coupon_code=None, discount_amount=0) -> int:
        """
        cart_items: list of dict {'ad': name, 'fiyat': total_item_price, 'adet': quantity}
        """
        raw_total = sum(item['fiyat'] for item in cart_items)
        final_total = raw_total - discount_amount
        if final_total < 0: final_total = 0

        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (customer_name, phone, delivery_method, total_price, status, note, coupon_code, discount_amount)
            VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?)
        ''', (customer_name, phone, delivery_method, final_total, note, coupon_code, discount_amount))
        
        order_id = cursor.lastrowid
        
        # Update coupon usage if applicable
        if coupon_code:
            cursor.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code = ?", (coupon_code,))

        for item in cart_items:
            # Note: The bot passes 'fiyat' as total for that line item. 
            # We should probably calculate unit price.
            unit_price = item['fiyat'] / item['adet'] if item['adet'] > 0 else 0
            
            # Fetch category name for reporting
            cat_name = "Diğer"
            if 'id' in item:
                 cursor.execute("SELECT c.name FROM products p JOIN categories c ON p.category_id = c.id WHERE p.id=?", (item['id'],))
                 res = cursor.fetchone()
                 if res: cat_name = res[0]

            cursor.execute('''
                INSERT INTO order_items (order_id, product_name, category_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, item['ad'], cat_name, item['adet'], unit_price))
            
            # Decrease Stock using ID if available, else name
            if 'id' in item:
                cursor.execute('''
                    UPDATE products SET stock = stock - ? WHERE id = ?
                ''', (item['adet'], item['id']))
            else:
                cursor.execute('''
                    UPDATE products SET stock = stock - ? WHERE name = ?
                ''', (item['adet'], item['ad']))
            
        conn.commit()
        conn.close()
        return order_id

    def get_orders(self, status_filter=None):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status_filter:
            cursor.execute("SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC", (status_filter,))
        else:
            cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
            
        rows = cursor.fetchall()
        orders = []
        for row in rows:
            o = dict(row)
            # Fetch items
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o['id'],))
            item_rows = cursor.fetchall()
            o['items'] = [dict(i) for i in item_rows]
            orders.append(o)
        
        conn.close()
        return orders

    def update_order_status(self, order_id, new_status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()

    def create_historical_order(self, customer_name, total_price, created_at):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (customer_name, total_price, status, created_at, delivery_method)
            VALUES (?, ?, 'Delivered', ?, 'Geçmiş Ekleme')
        ''', (customer_name, total_price, created_at))
        conn.commit()
        conn.close()

    def update_order_details(self, order_id, customer_name, total_price, created_at):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders
            SET customer_name=?, total_price=?, created_at=?
            WHERE id=?
        ''', (customer_name, total_price, created_at, order_id))
        conn.commit()
        conn.close()

    def get_product_sales_report(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                oi.product_name,
                SUM(oi.quantity) as total_qty,
                SUM(oi.price * oi.quantity) as total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status = 'Delivered'
            GROUP BY oi.product_name
            ORDER BY total_revenue DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_total_income(self, category_filter=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category_filter:
            # Join orders and order_items
            cursor.execute('''
                SELECT SUM(oi.price * oi.quantity)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'Delivered' AND oi.category_name = ?
            ''', (category_filter,))
        else:
            cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'Delivered'")
            
        res = cursor.fetchone()[0]
        conn.close()
        return res if res else 0.0

    def add_expense(self, category_name, description, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (category_name, description, amount) VALUES (?, ?, ?)", (category_name, description, amount))
        conn.commit()
        conn.close()

    def get_total_expenses(self, category_filter=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if category_filter:
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE category_name = ?", (category_filter,))
        else:
            cursor.execute("SELECT SUM(amount) FROM expenses")
        res = cursor.fetchone()[0]
        conn.close()
        return res if res else 0.0
        
    def get_expenses(self, category_filter=None):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if category_filter:
            cursor.execute("SELECT * FROM expenses WHERE category_name = ? ORDER BY created_at DESC", (category_filter,))
        else:
            cursor.execute("SELECT * FROM expenses ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
        
    def get_daily_income(self, days=7):
        # Helper for charts
        conn = self.get_connection()
        cursor = conn.cursor()
        # Get last N days income grouped by date
        # SQLite 'date(created_at)' truncates timestamp
        cursor.execute(f'''
            SELECT date(created_at) as d, SUM(total_price) 
            FROM orders 
            WHERE status = 'Delivered' 
            AND created_at >= date('now', '-{days} days')
            GROUP BY d
            ORDER BY d ASC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return rows # list of (date_str, total)

    # --- Coupon Methods ---
    def add_coupon(self, code, percent, limit=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO coupons (code, discount_percent, usage_limit) VALUES (?, ?, ?)", 
                           (code, percent, limit))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_coupons(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM coupons")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_coupon(self, code):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM coupons WHERE code = ?", (code,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def toggle_coupon(self, code, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE coupons SET is_active = ? WHERE code = ?", (status, code))
        conn.commit()
        conn.close()

    def delete_coupon(self, code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM coupons WHERE code = ?", (code,))
        conn.commit()
        conn.close()

    # --- Settings Methods ---
    def get_setting(self, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else ""

    def set_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
