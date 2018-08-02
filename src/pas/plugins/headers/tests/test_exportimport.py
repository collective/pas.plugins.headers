# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING  # noqa
from pas.plugins.headers.utils import get_plugin

import json
import unittest


class FauxContext(object):

    def __init__(self, site=None, content=None):
        self.site = site
        self.content = content

    def getSite(self):
        return self.site

    def getLogger(self, name):
        import logging
        return logging.getLogger(name)

    def readDataFile(self, name):
        assert name == 'pas.plugins.headers.json'
        return self.content


class TestImport(unittest.TestCase):
    """Test our import step."""

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.plugin = get_plugin(self.portal)

    def _makeContext(self, content=None):
        """Create a fake portal_setup context."""
        return FauxContext(site=self.portal, content=content)

    def _configurePlugin(self):
        """Give the plugin some data."""
        self.plugin.deny_unauthorized = True
        self.plugin.memberdata_to_header = ('foo|bar',)
        self.plugin.redirect_url = 'https://example.org'
        self.plugin.required_headers = ('foo',)
        self.plugin.userid_header = 'foo'

    def assert_plugin_has_test_settings(self):
        """Assert that the plugin has the settings from _configurePlugin."""
        self.assertTrue(self.plugin.deny_unauthorized)
        self.assertTupleEqual(self.plugin.memberdata_to_header, ('foo|bar',))
        self.assertEqual(self.plugin.redirect_url, 'https://example.org')
        self.assertTupleEqual(self.plugin.required_headers, ('foo',))
        self.assertEqual(self.plugin.userid_header, 'foo')

    def assert_plugin_has_default_settings(self):
        """Assert that the plugin has the default settings."""
        from pas.plugins.headers.plugins import HeaderPlugin
        self.assertEqual(
            self.plugin.deny_unauthorized,
            HeaderPlugin.deny_unauthorized,
        )
        self.assertTupleEqual(
            self.plugin.memberdata_to_header,
            HeaderPlugin.memberdata_to_header,
        )
        self.assertEqual(
            self.plugin.redirect_url,
            HeaderPlugin.redirect_url,
        )
        self.assertTupleEqual(
            self.plugin.required_headers,
            HeaderPlugin.required_headers,
        )
        self.assertEqual(
            self.plugin.userid_header,
            HeaderPlugin.userid_header,
        )

    def test_import_no_file(self):
        """When the import file is not there, nothing should go wrong."""
        from pas.plugins.headers.exportimport import import_properties
        import_properties(self._makeContext())

    def test_import_empty(self):
        """When the import file is empty, nothing should go wrong."""
        from pas.plugins.headers.exportimport import import_properties
        import_properties(self._makeContext(''))

    def test_import_full(self):
        """Test a full import."""
        from pas.plugins.headers.exportimport import import_properties
        settings = {
            'deny_unauthorized': True,
            'memberdata_to_header': [
                'uid|PROFILE_uid',
                'fullname|PROFILE_firstname PROFILE_lastname',
                'role|PROFILE_role|lower'
            ],
            'redirect_url': 'https://maurits.vanrees.org',
            'required_headers': [
                'uid',
                'role'
            ],
            'userid_header': 'uid'
        }
        import_properties(self._makeContext(json.dumps(settings)))
        self.assertTrue(self.plugin.deny_unauthorized)
        self.assertTupleEqual(
            self.plugin.memberdata_to_header,
            (
                'uid|PROFILE_uid',
                'fullname|PROFILE_firstname PROFILE_lastname',
                'role|PROFILE_role|lower',
            ),
        )
        self.assertEqual(
            self.plugin.redirect_url, 'https://maurits.vanrees.org')
        self.assertTupleEqual(
            self.plugin.required_headers,
            ('uid', 'role'),
        )
        self.assertEqual(self.plugin.userid_header, 'uid')
        # We want string, not unicode: when you save the properties form
        # in the ZMI, you always get a string.
        # self.assertIsInstance(self.plugin.required_headers[0], str) TODO

    def test_import_purge_false(self):
        """Test purge=false."""
        from pas.plugins.headers.exportimport import import_properties
        self._configurePlugin()
        settings = {'purge': False}
        import_properties(self._makeContext(json.dumps(settings)))
        self.assert_plugin_has_test_settings()

    def test_import_purge_true(self):
        """Test purge=true."""
        from pas.plugins.headers.exportimport import import_properties
        self._configurePlugin()
        settings = {'purge': True}
        import_properties(self._makeContext(json.dumps(settings)))
        self.assert_plugin_has_default_settings()

    def test_import_purge_and_set(self):
        """Test purge=true and setting some values."""
        from pas.plugins.headers.exportimport import import_properties
        self._configurePlugin()
        settings = {
            'purge': True,
            'deny_unauthorized': True,
            'userid_header': 'my_uid',
        }
        import_properties(self._makeContext(json.dumps(settings)))
        self.assertTrue(self.plugin.deny_unauthorized)
        self.assertTupleEqual(self.plugin.memberdata_to_header, ())
        self.assertEqual(self.plugin.redirect_url, '')
        self.assertTupleEqual(self.plugin.required_headers, ())
        self.assertEqual(self.plugin.userid_header, 'my_uid')
