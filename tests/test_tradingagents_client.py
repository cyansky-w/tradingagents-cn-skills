import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tradingagents_client import TradingAgentsError, load_config


class LoadConfigTests(unittest.TestCase):
    def test_load_config_requires_base_url(self) -> None:
        with patch.dict(os.environ, {"LOCALAPPDATA": "C:/temp"}, clear=True):
            with self.assertRaises(TradingAgentsError) as ctx:
                load_config()

        self.assertIn("TRADINGAGENTS_BASE_URL", str(ctx.exception))

    def test_load_config_uses_only_explicit_environment_values(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LOCALAPPDATA": "C:/temp",
                "TRADINGAGENTS_BASE_URL": "https://example.test/api/",
                "TRADINGAGENTS_USERNAME": "alice",
                "TRADINGAGENTS_PASSWORD": "secret",
                "TRADINGAGENTS_BEARER_TOKEN": "token-123",
            },
            clear=True,
        ):
            config = load_config()

        self.assertEqual(config.base_url, "https://example.test/api")
        self.assertEqual(config.username, "alice")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.bearer_token, "token-123")


if __name__ == "__main__":
    unittest.main()
