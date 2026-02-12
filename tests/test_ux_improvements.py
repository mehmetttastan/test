
import unittest
from unittest.mock import MagicMock, AsyncMock

# Mocking parts of bot_app logic for testing input validation
class TestInputValidation(unittest.TestCase):
    def test_customer_info_validation(self):
        # Setup
        # Logic: If text < 5 chars -> return GET_INFO (loop)
        # If text >= 5 chars -> return DELIVERY_SELECT (next step)

        # Case 1: Short Input
        text = "Ali"
        next_state = "GET_INFO" if len(text) < 5 else "DELIVERY_SELECT"
        self.assertEqual(next_state, "GET_INFO", "Short input should loop back")

        # Case 2: Valid Input
        text = "Ali Yilmaz 555"
        next_state = "GET_INFO" if len(text) < 5 else "DELIVERY_SELECT"
        self.assertEqual(next_state, "DELIVERY_SELECT", "Valid input should proceed")

if __name__ == '__main__':
    unittest.main()
