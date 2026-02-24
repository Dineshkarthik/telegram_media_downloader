"""Unit tests for webui package modules.

These tests require NiceGUI which is only available on Python >= 3.10.
They are automatically skipped on older Python versions.
"""

import sys
import unittest

import pytest

# Skip the entire module if NiceGUI is not installed (Python < 3.10)
nicegui = pytest.importorskip("nicegui", reason="NiceGUI requires Python >= 3.10")

from unittest import mock


class TestStyles(unittest.TestCase):
    """Tests for webui.styles module."""

    def test_premium_css_is_string(self):
        from webui.styles import PREMIUM_CSS

        self.assertIsInstance(PREMIUM_CSS, str)

    def test_premium_css_contains_design_tokens(self):
        from webui.styles import PREMIUM_CSS

        self.assertIn("--surface", PREMIUM_CSS)
        self.assertIn("--accent", PREMIUM_CSS)
        self.assertIn("--text-primary", PREMIUM_CSS)

    def test_premium_css_contains_dark_mode(self):
        from webui.styles import PREMIUM_CSS

        self.assertIn("body.body--dark", PREMIUM_CSS)

    def test_premium_css_contains_style_tags(self):
        from webui.styles import PREMIUM_CSS

        self.assertIn("<style>", PREMIUM_CSS)
        self.assertIn("</style>", PREMIUM_CSS)

    def test_premium_css_contains_font_link(self):
        from webui.styles import PREMIUM_CSS

        self.assertIn("fonts.googleapis.com", PREMIUM_CSS)
        self.assertIn("Inter", PREMIUM_CSS)


class TestTour(unittest.TestCase):
    """Tests for webui.tour module."""

    def test_tour_steps_is_list(self):
        from webui.tour import TOUR_STEPS

        self.assertIsInstance(TOUR_STEPS, list)

    def test_tour_steps_not_empty(self):
        from webui.tour import TOUR_STEPS

        self.assertGreater(len(TOUR_STEPS), 0)

    def test_tour_steps_have_required_keys(self):
        from webui.tour import TOUR_STEPS

        required_keys = {"icon", "title", "body"}
        for i, step in enumerate(TOUR_STEPS):
            for key in required_keys:
                self.assertIn(
                    key, step, f"Step {i} ('{step.get('title', '?')}') missing '{key}'"
                )

    def test_first_step_is_welcome(self):
        from webui.tour import TOUR_STEPS

        self.assertIn("Welcome", TOUR_STEPS[0]["title"])

    def test_tour_steps_page_values_are_valid(self):
        from webui.tour import TOUR_STEPS

        valid_pages = {"config", "execution", "history"}
        for step in TOUR_STEPS:
            if "page" in step:
                self.assertIn(
                    step["page"],
                    valid_pages,
                    f"Step '{step['title']}' has invalid page '{step['page']}'",
                )

    def test_tour_step_bodies_use_markdown_lists(self):
        """Ensure bullet points use markdown - syntax, not • characters."""
        from webui.tour import TOUR_STEPS

        for step in TOUR_STEPS:
            self.assertNotIn(
                "•",
                step["body"],
                f"Step '{step['title']}' uses '•' instead of markdown '- '",
            )

    def test_build_tour_is_callable(self):
        from webui.tour import build_tour

        self.assertTrue(callable(build_tour))


class TestConfigTab(unittest.TestCase):
    """Tests for webui.config_tab module."""

    def test_build_config_tab_is_callable(self):
        from webui.config_tab import build_config_tab

        self.assertTrue(callable(build_config_tab))


class TestExecutionTab(unittest.TestCase):
    """Tests for webui.execution_tab module."""

    def test_build_execution_tab_is_callable(self):
        from webui.execution_tab import build_execution_tab

        self.assertTrue(callable(build_execution_tab))


class TestHistoryTab(unittest.TestCase):
    """Tests for webui.history_tab module."""

    def test_build_history_tab_is_callable(self):
        from webui.history_tab import build_history_tab

        self.assertTrue(callable(build_history_tab))


class TestConfigManager(unittest.TestCase):
    """Test that config_manager is importable and correctly structured."""

    def test_load_config_is_callable(self):
        from config_manager import load_config

        self.assertTrue(callable(load_config))

    def test_save_config_is_callable(self):
        from config_manager import save_config

        self.assertTrue(callable(save_config))


if __name__ == "__main__":
    unittest.main()
