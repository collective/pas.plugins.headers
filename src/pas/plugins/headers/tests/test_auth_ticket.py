# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING  # noqa
from pas.plugins.headers.utils import PLUGIN_ID
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import unittest


class TestAuthTicket(unittest.TestCase):
    """Test that create_ticket works as intended."""

    layer = PAS_PLUGINS_HEADERS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.pas = self.portal.acl_users
        self.plugin = self.pas.request_headers
        self.plugin.create_ticket = True
        self.session = self.pas.session

    def test_auth_unknown_user(self):
        self.assertEqual(self.plugin.authenticateCredentials({
            'user_id': 'joe', 'extractor': PLUGIN_ID
        }), ('joe', 'joe'))
        response = self.portal.REQUEST.response
        self.assertNotIn('__ac', response.cookies)

    def test_auth_known_user(self):
        self.assertEqual(self.plugin.authenticateCredentials({
            'user_id': TEST_USER_ID, 'extractor': PLUGIN_ID
        }), (TEST_USER_ID, TEST_USER_ID))
        request = self.portal.REQUEST
        response = request.response
        self.assertIn('__ac', response.cookies)
        cookie = response.cookies['__ac']
        value = cookie.pop('value', None)
        self.assertIsNotNone(value)
        self.assertDictEqual(cookie, {'path': '/', 'secure': False, 'http_only': True, 'quoted': True})

        # Now set the cookie from the response on the request,
        # and see if plone.session can read it.
        request.cookies['__ac'] = value
        credentials = self.session.extractCredentials(request)
        self.assertTrue(credentials)
        result = self.session.authenticateCredentials(credentials)
        self.assertTrue(result)
        userid, login = result
        self.assertEqual(userid, TEST_USER_ID)
        self.assertEqual(login, TEST_USER_NAME)
