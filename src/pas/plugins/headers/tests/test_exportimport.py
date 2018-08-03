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
        self.exported = None

    def getSite(self):
        return self.site

    def getLogger(self, name):
        import logging
        return logging.getLogger(name)

    def readDataFile(self, name):
        assert name == 'pas.plugins.headers.json'
        return self.content

    def writeDataFile(self, filename, body, content_type):
        assert filename == 'pas.plugins.headers.json'
        assert content_type == 'application/json'
        self.exported = body

    def get_exported_data(self):
        return self.exported


class ExportImportBaseTestCase(unittest.TestCase):
    """Base test case with handy methods for testing our export and import."""

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
        self.plugin.allowed_roles = ('root',)
        self.plugin.deny_unauthorized = True
        self.plugin.memberdata_to_header = ('foo|bar',)
        self.plugin.redirect_url = 'https://example.org'
        self.plugin.required_headers = ('foo',)
        self.plugin.roles_header = 'humbug'
        self.plugin.userid_header = 'foo'

    def _removePlugin(self):
        """Remove the plugin."""
        from plone import api
        from pas.plugins.headers.utils import PLUGIN_ID
        pas = api.portal.get_tool('acl_users')
        pas._delObject(PLUGIN_ID)

    def assert_plugin_has_test_settings(self):
        """Assert that the plugin has the settings from _configurePlugin."""
        self.assertTupleEqual(self.plugin.allowed_roles, ('root',))
        self.assertTrue(self.plugin.deny_unauthorized)
        self.assertTupleEqual(self.plugin.memberdata_to_header, ('foo|bar',))
        self.assertEqual(self.plugin.redirect_url, 'https://example.org')
        self.assertTupleEqual(self.plugin.required_headers, ('foo',))
        self.assertEqual(self.plugin.roles_header, 'humbug')
        self.assertEqual(self.plugin.userid_header, 'foo')

    def assert_plugin_has_default_settings(self):
        """Assert that the plugin has the default settings."""
        from pas.plugins.headers.plugins import HeaderPlugin
        self.assertTupleEqual(
            self.plugin.allowed_roles,
            HeaderPlugin.allowed_roles,
        )
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
            self.plugin.roles_header,
            HeaderPlugin.roles_header,
        )
        self.assertEqual(
            self.plugin.userid_header,
            HeaderPlugin.userid_header,
        )


class TestImport(ExportImportBaseTestCase):
    """Test our import step."""

    def test_import_step_in_profile(self):
        from plone.app.testing import applyProfile
        applyProfile(self.portal, 'pas.plugins.headers.tests:test')
        self.assertTupleEqual(
            self.plugin.allowed_roles,
            (
                'Member',
                'Zebra',
            ),
        )
        self.assertTrue(self.plugin.deny_unauthorized)
        self.assertTupleEqual(
            self.plugin.memberdata_to_header,
            (
                'uid|HEADER_uid|lower',
                'fullname|HEADER_firstname HEADER_lastname',
            ),
        )
        self.assertEqual(
            self.plugin.redirect_url, 'https://maurits.vanrees.org')
        self.assertTupleEqual(self.plugin.required_headers, ('uid', 'test'))
        self.assertEqual(self.plugin.roles_header, 'roles')
        self.assertEqual(self.plugin.userid_header, 'uid')

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
            'allowed_roles': ['missile', 'target'],
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
            'roles_header': 'portal_roles',
            'userid_header': 'uid'
        }
        import_properties(self._makeContext(json.dumps(settings)))
        self.assertTupleEqual(
            self.plugin.allowed_roles,
            ('missile', 'target'),
        )
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
        self.assertEqual(self.plugin.roles_header, 'portal_roles')
        self.assertEqual(self.plugin.userid_header, 'uid')

        # Explicitly test the types.
        # We want string, not unicode: when you save the properties form
        # in the ZMI, you always get a string.
        # And we want tuples, not lists.
        self.assertIsInstance(self.plugin.allowed_roles, tuple)
        self.assertIsInstance(self.plugin.allowed_roles[0], str)
        self.assertIsInstance(self.plugin.deny_unauthorized, bool)
        self.assertIsInstance(self.plugin.memberdata_to_header, tuple)
        self.assertIsInstance(self.plugin.memberdata_to_header[0], str)
        self.assertIsInstance(self.plugin.redirect_url, str)
        self.assertIsInstance(self.plugin.required_headers, tuple)
        self.assertIsInstance(self.plugin.required_headers[0], str)
        self.assertIsInstance(self.plugin.roles_header, str)
        self.assertIsInstance(self.plugin.userid_header, str)

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

    def test_import_no_plugin(self):
        """Test that import does not fail when plugin is not there."""
        from pas.plugins.headers.exportimport import import_properties
        from pas.plugins.headers.utils import get_plugin
        self._removePlugin()
        settings = {
            'purge': True,
            'deny_unauthorized': True,
            'userid_header': 'my_uid',
        }
        import_properties(self._makeContext(json.dumps(settings)))
        self.assertIsNone(get_plugin(self.portal))

    def test_import_bad_json(self):
        """Test how import handles a bad json."""
        from pas.plugins.headers.exportimport import import_properties
        self._configurePlugin()
        with self.assertRaises(ValueError):
            import_properties(self._makeContext(
                '{"userid_header": "missing end quote}'))

    def test_import_non_dictionary(self):
        """Test how import handles a file without a dictionary."""
        from pas.plugins.headers.exportimport import import_properties
        self._configurePlugin()
        settings = [{'userid_header': 'header_user'}]
        with self.assertRaises(ValueError):
            import_properties(self._makeContext(json.dumps(settings)))
        self.assertEqual(self.plugin.userid_header, 'foo')

    def test_import_unknown_property(self):
        """Test that import does not fail for an unknown property."""
        from pas.plugins.headers.exportimport import import_properties
        settings = {
            'unknown': 'hello',
            'userid_header': 'my_uid',
        }
        import_properties(self._makeContext(json.dumps(settings)))
        self.assertEqual(self.plugin.userid_header, 'my_uid')
        marker = object()
        self.assertIs(getattr(self.plugin, 'unknown', marker), marker)


class TestExport(ExportImportBaseTestCase):
    """Test our export step."""

    def test_export_default(self):
        from pas.plugins.headers.exportimport import export_properties
        context = self._makeContext()
        export_properties(context)
        # Here we test the *exact* file contents, including indentation.
        # Well... there is trailing white space, so let's ignore indentation.
        self.assertEqual(
            '\n'.join([line.strip() for line in
                       context.get_exported_data().splitlines()]),
            """{
"allowed_roles": [],
"deny_unauthorized": false,
"memberdata_to_header": [],
"redirect_url": "",
"required_headers": [],
"roles_header": "",
"userid_header": ""
}""",
        )
        self.assertDictEqual(
            json.loads(context.get_exported_data()),
            {
                'allowed_roles': [],
                'deny_unauthorized': False,
                'memberdata_to_header': [],
                'redirect_url': '',
                'required_headers': [],
                'roles_header': '',
                'userid_header': '',
            },
        )

    def test_export_test_settings(self):
        from pas.plugins.headers.exportimport import export_properties
        self._configurePlugin()
        context = self._makeContext()
        export_properties(context)
        self.assertIsInstance(context.get_exported_data(), str)
        self.assertDictEqual(
            json.loads(context.get_exported_data()),
            {
                'allowed_roles': ['root'],
                'deny_unauthorized': True,
                'memberdata_to_header': ['foo|bar'],
                'redirect_url': 'https://example.org',
                'required_headers': ['foo'],
                'roles_header': 'humbug',
                'userid_header': 'foo',
            },
        )

    def test_export_no_plugin(self):
        """Test that export does not fail when plugin is not there."""
        from pas.plugins.headers.exportimport import export_properties
        self._removePlugin()
        context = self._makeContext()
        export_properties(context)
        self.assertIsNone(context.get_exported_data())
