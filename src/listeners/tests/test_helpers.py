import unittest
from unittest.mock import patch

from src.listeners.helpers import get_random_user_agent, user_agents


class RandomUserAgentTestCase(unittest.TestCase):
    def test_returns_random_user_agent(self):
        user_agent = get_random_user_agent()
        self.assertIsInstance(user_agent, str)
        self.assertIn(user_agent, user_agents)

    def test_returns_string_user_agent(self):
        user_agent = get_random_user_agent()
        self.assertIsInstance(user_agent, str)

