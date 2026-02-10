
import sqlite3
import sys

def show_expenses():
    if not os.path.exists("shop.db"):
        print("Database not found.")
        return

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    print("--- ALL EXPENSES IN DB ---")
    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()

    if not rows:
        print("No expenses found.")
    else:
        print(f"{'ID':<5} | {'Category':<15} | {'Amount':<10} | {'Desc'}")
        print("-" * 50)
        for r in rows:
            # id, cat, desc, amt, date
            print(f"{r[0]:<5} | {r[1]:<15} | {r[3]:<10} | {r[2]}")

    conn.close()

if __name__ == "__main__":
    import os
    show_expenses()
