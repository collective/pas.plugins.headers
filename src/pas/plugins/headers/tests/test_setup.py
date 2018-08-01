# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestSetup(unittest.TestCase):
    """Test that pas.plugins.headers is properly installed."""

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if pas.plugins.headers is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'pas.plugins.headers'))

    def test_plugin_added(self):
        """Test if the plugin is added to acl_users."""
        from pas.plugins.headers.plugins import HeaderPlugin
        pas = api.portal.get_tool('acl_users')
        plugin_id = 'request_headers'
        self.assertIn(plugin_id, pas.objectIds())
        plugin = getattr(pas, plugin_id)
        self.assertIsInstance(plugin, HeaderPlugin)


class TestUninstall(unittest.TestCase):

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['pas.plugins.headers'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if pas.plugins.headers is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'pas.plugins.headers'))

    def test_plugin_removed(self):
        """Test if the plugin is removed from acl_users."""
        pas = api.portal.get_tool('acl_users')
        plugin_id = 'request_headers'
        self.assertNotIn(plugin_id, pas.objectIds())
