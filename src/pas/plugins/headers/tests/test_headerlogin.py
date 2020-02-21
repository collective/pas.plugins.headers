# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING  # noqa
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.z2 import Browser
from zExceptions import Forbidden

import transaction
import unittest


class TestHeaderLogin(unittest.TestCase):
    """Test that the headerlogin page works as intended."""

    layer = PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.plugin = self.portal.acl_users.request_headers
        self.browser = Browser(app)
        self.browser.handleErrors = False

    def test_redirect_anonymous(self):
        with self.assertRaises(Forbidden):
            self.browser.open(self.portal_url + '/headerlogin')

    def test_redirect_basic_auth(self):
        self.browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url)

    def test_redirect_userid_header(self):
        self.plugin.userid_header = 'UID'
        transaction.commit()
        self.browser.addHeader('UID', SITE_OWNER_NAME)
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url)

    def test_redirect_came_from_good(self):
        self.browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )
        self.browser.open('{}/headerlogin?came_from={}/view'.format(self.portal_url, self.portal_url))
        self.assertEqual(self.browser.url, self.portal_url + '/view')

    def test_redirect_came_from_bad(self):
        self.browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )
        self.browser.open(self.portal_url + '/headerlogin?came_from=http://attacker.com')
        self.assertEqual(self.browser.url, self.portal_url)
