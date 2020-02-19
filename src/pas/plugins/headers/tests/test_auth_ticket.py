# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_INTEGRATION_TESTING  # noqa
from pas.plugins.headers.utils import PLUGIN_ID
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

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
        response = self.portal.REQUEST.response
        self.assertIn('__ac', response.cookies)
        cookie = response.cookies['__ac']
        value = cookie.pop('value', None)
        self.assertIsNotNone(value)
        self.assertDictEqual(cookie, {'path': '/', 'secure': False, 'http_only': True, 'quoted': True})
        import binascii
        ticket = binascii.a2b_base64(value)
        ticket_data = self.session._validateTicket(ticket)
        self.assertTrue(ticket_data)
        (digest, userid, tokens, user_data, timestamp) = ticket_data
        self.assertEqual(userid, TEST_USER_ID)



