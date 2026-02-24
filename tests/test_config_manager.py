"""Unit tests for config_manager module."""

import os
import tempfile
import unittest
from unittest import mock

import yaml

import config_manager


class ConfigManagerTestCase(unittest.TestCase):
    """Tests for load_config / save_config."""

    def setUp(self):
        """Create a temporary config file for each test."""
        self._tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        self._tmp.close()
        self._orig_path = config_manager.CONFIG_PATH
        config_manager.CONFIG_PATH = self._tmp.name

    def tearDown(self):
        config_manager.CONFIG_PATH = self._orig_path
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    # ── load_config ──

    def test_load_config_returns_dict(self):
        """load_config should return a dict from a valid YAML file."""
        with open(self._tmp.name, "w") as f:
            yaml.dump({"api_id": 123, "api_hash": "abc"}, f)

        result = config_manager.load_config()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["api_id"], 123)
        self.assertEqual(result["api_hash"], "abc")

    def test_load_config_empty_file_returns_empty_dict(self):
        """load_config should return {} for an empty YAML file."""
        with open(self._tmp.name, "w") as f:
            f.write("")

        result = config_manager.load_config()
        self.assertEqual(result, {})

    def test_load_config_preserves_nested_structure(self):
        """load_config should preserve nested dicts and lists."""
        data = {
            "chats": [
                {"chat_id": 111, "last_read_message_id": 0},
                {"chat_id": 222, "last_read_message_id": 50},
            ],
            "media_types": ["photo", "video"],
        }
        with open(self._tmp.name, "w") as f:
            yaml.dump(data, f)

        result = config_manager.load_config()
        self.assertEqual(len(result["chats"]), 2)
        self.assertEqual(result["chats"][0]["chat_id"], 111)
        self.assertListEqual(result["media_types"], ["photo", "video"])

    def test_load_config_file_not_found_raises(self):
        """load_config should raise FileNotFoundError for a missing file."""
        config_manager.CONFIG_PATH = "/nonexistent/path/config.yaml"
        with self.assertRaises(FileNotFoundError):
            config_manager.load_config()

    # ── save_config ──

    def test_save_config_writes_yaml(self):
        """save_config should write valid YAML to disk."""
        data = {"api_id": 999, "api_hash": "xyz", "media_types": ["photo"]}
        config_manager.save_config(data)

        with open(self._tmp.name, "r") as f:
            loaded = yaml.safe_load(f)

        self.assertEqual(loaded["api_id"], 999)
        self.assertEqual(loaded["api_hash"], "xyz")
        self.assertListEqual(loaded["media_types"], ["photo"])

    def test_save_config_overwrites_existing(self):
        """save_config should fully overwrite the file."""
        config_manager.save_config({"old_key": "old_value"})
        config_manager.save_config({"new_key": "new_value"})

        result = config_manager.load_config()
        self.assertNotIn("old_key", result)
        self.assertEqual(result["new_key"], "new_value")

    def test_save_config_no_sort_keys(self):
        """save_config should not sort keys (preserves insertion order)."""
        from collections import OrderedDict

        data = OrderedDict([("z_key", 1), ("a_key", 2), ("m_key", 3)])
        config_manager.save_config(dict(data))

        with open(self._tmp.name, "r") as f:
            content = f.read()

        # z_key should appear before a_key in the output
        self.assertLess(content.index("z_key"), content.index("a_key"))

    # ── round-trip ──

    def test_round_trip(self):
        """save_config → load_config should preserve data."""
        original = {
            "api_id": 42,
            "api_hash": "deadbeef",
            "chats": [{"chat_id": -100123, "last_read_message_id": 99}],
            "media_types": ["photo", "video", "document"],
            "download_delay": [1, 5],
        }
        config_manager.save_config(original)
        loaded = config_manager.load_config()
        self.assertEqual(loaded, original)


if __name__ == "__main__":
    unittest.main()
