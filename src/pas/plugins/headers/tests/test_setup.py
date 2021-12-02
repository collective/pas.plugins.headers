# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


try:
    # Plone 5.1+
    from Products.CMFPlone.utils import get_installer
except ImportError:
    # Plone 5.0/4.3
    def get_installer(context, request=None):
        return api.portal.get_tool('portal_quickinstaller')


class TestSetup(unittest.TestCase):
    """Test that pas.plugins.headers is properly installed."""

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal)

    def test_product_installed(self):
        """Test if pas.plugins.headers is installed."""
        if hasattr(self.installer, "is_product_installed"):
            installed = self.installer.is_product_installed(
                'pas.plugins.headers')
        else:
            installed = self.installer.isProductInstalled(
                'pas.plugins.headers')
        self.assertTrue(installed)

    def test_plugin_added(self):
        """Test if the plugin is added to acl_users."""
        from pas.plugins.headers.plugins import HeaderPlugin
        from pas.plugins.headers.utils import PLUGIN_ID
        pas = api.portal.get_tool('acl_users')
        self.assertIn(PLUGIN_ID, pas.objectIds())
        plugin = getattr(pas, PLUGIN_ID)
        self.assertIsInstance(plugin, HeaderPlugin)

    def test_double_install(self):
        # A double install should not cause trouble.
        from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
        from pas.plugins.headers.utils import PLUGIN_ID
        pas = api.portal.get_tool('acl_users')
        pas._delObject(PLUGIN_ID)
        pas._setObject(PLUGIN_ID, BasePlugin())
        from pas.plugins.headers.setuphandlers import post_install
        with self.assertRaises(ValueError):
            post_install(self.portal)

    def test_uninstall_with_bad_plugin(self):
        # When a different plugin with 'our' id is found, we do not remove it.
        from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
        from pas.plugins.headers.utils import PLUGIN_ID
        pas = api.portal.get_tool('acl_users')
        pas._delObject(PLUGIN_ID)
        pas._setObject(PLUGIN_ID, BasePlugin())
        from pas.plugins.headers.setuphandlers import uninstall
        uninstall(self.portal)
        self.assertIn(PLUGIN_ID, pas.objectIds())


class TestUninstall(unittest.TestCase):

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal)
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        if hasattr(self.installer, "uninstall_product"):
            self.installer.uninstall_product('pas.plugins.headers')
        else:
            self.installer.uninstallProducts(['pas.plugins.headers'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if pas.plugins.headers is cleanly uninstalled."""
        if hasattr(self.installer, "is_product_installed"):
            installed = self.installer.is_product_installed(
                'pas.plugins.headers')
        else:
            installed = self.installer.isProductInstalled(
                'pas.plugins.headers')
        self.assertFalse(installed)

    def test_plugin_removed(self):
        """Test if the plugin is removed from acl_users."""
        from pas.plugins.headers.utils import PLUGIN_ID
        pas = api.portal.get_tool('acl_users')
        self.assertNotIn(PLUGIN_ID, pas.objectIds())

    def test_double_uninstall(self):
        # A double uninstall should not cause trouble.
        from pas.plugins.headers.setuphandlers import uninstall
        uninstall(self.portal)
