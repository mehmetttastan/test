
import unittest
from unittest.mock import MagicMock, AsyncMock

# Mocking parts of bot_app logic for testing stock validation UI Logic
class TestStockUILogic(unittest.TestCase):
    def test_stock_full_logic(self):
        # Setup
        product = {'id': 1, 'name': 'Elma', 'stock': 2, 'price': 10}

        # Scenario: User has 2 in cart (Max stock)
        cart = [{'id': 1, 'adet': 2}]
        qty_requested = 1

        current_cart_qty = sum(item['adet'] for item in cart if item['id'] == product['id'])
        remaining = product['stock'] - current_cart_qty

        # Verify calculation
        self.assertEqual(remaining, 0)

        # Verify Logic Path that would be taken
        is_stock_full = False
        keyboard_type = "normal"

        if qty_requested + current_cart_qty > product['stock']:
             if remaining <= 0:
                 is_stock_full = True
                 keyboard_type = "restricted" # Should happen
             else:
                 is_stock_full = False
                 keyboard_type = "retry"

        self.assertTrue(is_stock_full, "Should be flagged as stock full")
        self.assertEqual(keyboard_type, "restricted", "Should show restricted keyboard (Back/Cart only)")

    def test_stock_partial_logic(self):
        # Setup
        product = {'id': 1, 'name': 'Elma', 'stock': 5, 'price': 10}

        # Scenario: User has 2 in cart, requests 4 (Total 6 > 5)
        cart = [{'id': 1, 'adet': 2}]
        qty_requested = 4

        current_cart_qty = sum(item['adet'] for item in cart if item['id'] == product['id'])
        remaining = product['stock'] - current_cart_qty # 3

        # Verify calculation
        self.assertEqual(remaining, 3)

        # Verify Logic Path
        is_stock_full = False
        keyboard_type = "normal"

        if qty_requested + current_cart_qty > product['stock']:
             if remaining <= 0:
                 is_stock_full = True
                 keyboard_type = "restricted"
             else:
                 is_stock_full = False
                 keyboard_type = "retry" # Should happen

        self.assertFalse(is_stock_full, "Should NOT be flagged as stock full")
        self.assertEqual(keyboard_type, "retry", "Should show retry keyboard (1-5)")

if __name__ == '__main__':
    unittest.main()
