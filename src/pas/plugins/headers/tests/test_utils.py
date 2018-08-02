# -*- coding: utf-8 -*-
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


class TestUtils(unittest.TestCase):
    """Test that utils.py works."""

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']

    def test_get_plugin_no_pas(self):
        from pas.plugins.headers.utils import get_plugin
        self.portal._delObject('acl_users')
        self.assertIsNone(get_plugin(self.portal))

    def test_get_plugin_removed(self):
        from pas.plugins.headers.utils import get_plugin
        from pas.plugins.headers.utils import PLUGIN_ID
        pas = api.portal.get_tool('acl_users')
        pas._delObject(PLUGIN_ID)
        self.assertIsNone(get_plugin(self.portal))

    def test_get_plugin_with_bad_plugin(self):
        from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
        from pas.plugins.headers.utils import PLUGIN_ID
        from pas.plugins.headers.utils import get_plugin
        pas = api.portal.get_tool('acl_users')
        pas._delObject(PLUGIN_ID)
        pas._setObject(PLUGIN_ID, BasePlugin())
        self.assertIsNone(get_plugin(self.portal))

    def test_get_plugin_proper(self):
        from pas.plugins.headers.utils import get_plugin
        from pas.plugins.headers.utils import PLUGIN_ID
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = get_plugin(self.portal)
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, PLUGIN_ID)
        self.assertIsInstance(plugin, HeaderPlugin)
        self.assertEqual(plugin, getattr(self.portal.acl_users, PLUGIN_ID))
