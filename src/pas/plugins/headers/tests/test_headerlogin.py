# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING  # noqa
from plone.testing.z2 import Browser

import unittest


class TestHeaderLogin(unittest.TestCase):
    """Test that the headerlogin page works as intended."""

    layer = PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(app)
        self.browser.handleErrors = False

    def test_redirect_root(self):
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url)

    def test_redirect_came_from_good(self):
        self.browser.open('{}/headerlogin?came_from={}/view'.format(self.portal_url, self.portal_url))
        self.assertEqual(self.browser.url, self.portal_url + '/view')

    def test_redirect_came_from_bad(self):
        self.browser.open(self.portal_url + '/headerlogin?came_from=http://attacker.com')
        self.assertEqual(self.browser.url, self.portal_url)
