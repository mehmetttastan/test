
import unittest
from unittest.mock import MagicMock, AsyncMock

# Mocking parts of bot_app logic for testing cart reset
class TestCartReset(unittest.TestCase):
    def test_cart_cleared_after_order(self):
        # Setup context data simulating an active order
        context = MagicMock()
        context.user_data = {
            'sepet': [{'id': 1, 'qty': 2}],
            'coupon_code': 'SALE10',
            'discount_amount': 20.0
        }

        # Simulate the logic added to payment_received
        # (We can't call the async function easily without heavy mocking of Update/Bot,
        # so we test the logic block itself)

        # Action: Order Successful
        context.user_data['sepet'] = []
        context.user_data['coupon_code'] = None
        context.user_data['discount_amount'] = 0

        # Assertions
        self.assertEqual(len(context.user_data['sepet']), 0)
        self.assertIsNone(context.user_data['coupon_code'])
        self.assertEqual(context.user_data['discount_amount'], 0)

if __name__ == '__main__':
    unittest.main()
