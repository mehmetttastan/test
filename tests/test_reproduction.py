
import unittest
from unittest.mock import MagicMock

# Mocking parts of bot_app logic for testing stock validation
class TestStockValidation(unittest.TestCase):
    def test_stock_validation_with_cart(self):
        # Setup
        product = {'id': 1, 'name': 'Elma', 'stock': 2, 'price': 10}

        # Case 1: Cart is empty, request 3 (Stock 2) -> Should Fail
        cart = []
        qty_requested = 3

        current_cart_qty = sum(item['adet'] for item in cart if item['id'] == product['id'])
        self.assertTrue(qty_requested + current_cart_qty > product['stock'])

        # Case 2: Cart is empty, request 2 (Stock 2) -> Should Pass
        qty_requested = 2
        self.assertFalse(qty_requested + current_cart_qty > product['stock'])

        # Case 3: Cart has 2, request 2 (Stock 2) -> Should Fail (Current Bug: logic checks qty > stock, 2 > 2 is False, so it passes)
        cart = [{'id': 1, 'adet': 2}]
        qty_requested = 2

        # The Buggy Logic
        buggy_check = qty_requested > product['stock']
        self.assertFalse(buggy_check, "Buggy logic currently allows this because 2 is not greater than 2")

        # The Correct Logic
        current_cart_qty = sum(item['adet'] for item in cart if item['id'] == product['id'])
        correct_check = (qty_requested + current_cart_qty) > product['stock']
        self.assertTrue(correct_check, "Correct logic should prevent this because 2+2=4 > 2")

if __name__ == '__main__':
    unittest.main()
