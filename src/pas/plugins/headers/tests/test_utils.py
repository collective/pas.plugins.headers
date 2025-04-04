from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

import unittest


class TestGetPlugin(unittest.TestCase):
    """Test that utils.py works."""

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]

    def test_get_plugin_no_pas(self):
        from pas.plugins.headers.utils import get_plugin

        self.portal._delObject("acl_users")
        self.assertIsNone(get_plugin(self.portal))

    def test_get_plugin_removed(self):
        from pas.plugins.headers.utils import get_plugin
        from pas.plugins.headers.utils import PLUGIN_ID

        pas = self.portal.acl_users
        pas._delObject(PLUGIN_ID)
        self.assertIsNone(get_plugin(self.portal))

    def test_get_plugin_with_bad_plugin(self):
        from pas.plugins.headers.utils import get_plugin
        from pas.plugins.headers.utils import PLUGIN_ID
        from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin

        pas = self.portal.acl_users
        pas._delObject(PLUGIN_ID)
        pas._setObject(PLUGIN_ID, BasePlugin())
        self.assertIsNone(get_plugin(self.portal))

    def test_get_plugin_proper(self):
        from pas.plugins.headers.plugins import HeaderPlugin
        from pas.plugins.headers.utils import get_plugin
        from pas.plugins.headers.utils import PLUGIN_ID

        plugin = get_plugin(self.portal)
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, PLUGIN_ID)
        self.assertIsInstance(plugin, HeaderPlugin)
        self.assertEqual(plugin, getattr(self.portal.acl_users, PLUGIN_ID))


class TestSafeMakeString(unittest.TestCase):
    """Test that utils.py works."""

    def test_safe_make_string(self):
        from pas.plugins.headers.utils import safe_make_string

        self.assertEqual(safe_make_string(b""), "")
        self.assertEqual(safe_make_string(""), "")
        self.assertEqual(safe_make_string(""), "")

        expected = "\xeb"
        self.assertEqual(safe_make_string(b"\xc3\xab"), expected)
        self.assertEqual(safe_make_string(expected), expected)
        self.assertEqual(safe_make_string("\xeb"), expected)

        self.assertEqual(
            safe_make_string([1, b"two", "three", "four"]), [1, "two", "three", "four"]
        )

        self.assertEqual(safe_make_string(0), 0)
        self.assertEqual(safe_make_string(None), None)
        self.assertEqual(safe_make_string([]), [])
        self.assertEqual(safe_make_string(()), [])
        self.assertEqual(safe_make_string(set()), [])
