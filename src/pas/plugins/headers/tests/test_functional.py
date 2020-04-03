# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from pas.plugins.headers.testing import PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING  # noqa
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing.z2 import Browser
from zExceptions import Forbidden
from zExceptions import Unauthorized

import transaction
import unittest


class TestUnderscoresAndDashes(unittest.TestCase):
    """Test how the plugin handles underscores and dashes.

    Headers are strange creatures.
    Dashes and underscores are not always allowed or advised.
    Both frontend servers and Zope can change headers or look up multiple variants.
    From zope.publisher.http.HTTPRequest.getHeader:

    def getHeader(self, name, default=None, literal=False):
        'See IHTTPRequest'
        environ = self._environ
        if not literal:
            name = name.replace('-', '_').upper()
        val = environ.get(name, None)
        if val is not None:
            return val
        if not name.startswith('HTTP_'):
            name='HTTP_%s' % name
        return environ.get(name, default)

    So let's do some tests.
    """

    layer = PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.plugin = self.portal.acl_users.request_headers

    def test_userid_header_dashes(self):
        self.plugin.userid_header = 'REMOTE-USER'
        transaction.commit()
        browser = Browser(self.app)
        browser.handleErrors = False
        browser.addHeader('REMOTE-USER', SITE_OWNER_NAME)
        browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(browser.url, self.portal_url)

    def test_userid_header_underscores(self):
        self.plugin.userid_header = 'REMOTE_USER'
        transaction.commit()
        browser = Browser(self.app)
        browser.handleErrors = False
        browser.addHeader('REMOTE_USER', SITE_OWNER_NAME)
        browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(browser.url, self.portal_url)

    def test_userid_header_underscores_http(self):
        self.plugin.userid_header = 'REMOTE_USER'
        transaction.commit()
        browser = Browser(self.app)
        browser.handleErrors = False
        # This will fail because it will really result in a
        # header HTTP_HTTP_REMOTE_USER.
        browser.addHeader('HTTP_REMOTE_USER', SITE_OWNER_NAME)
        browser.open(self.portal_url + '/headerlogin')
        # We are anonymous, so headerlogin redirects us to standard login.
        self.assertEqual(browser.url, self.portal_url + '/login')

    def test_userid_header_dash_underscore(self):
        self.plugin.userid_header = 'REMOTE-USER'
        transaction.commit()
        browser = Browser(self.app)
        browser.handleErrors = False
        browser.addHeader('REMOTE_USER', SITE_OWNER_NAME)
        browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(browser.url, self.portal_url)

    def test_userid_header_underscore_dash(self):
        self.plugin.userid_header = 'REMOTE_USER'
        transaction.commit()
        browser = Browser(self.app)
        browser.handleErrors = False
        browser.addHeader('REMOTE-USER', SITE_OWNER_NAME)
        browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(browser.url, self.portal_url)


class TestFull(unittest.TestCase):
    """Test that the package works as intended."""

    layer = PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.plugin = self.portal.acl_users.request_headers
        # Create a ticket, so known Plone users should remain authenticated
        # after the headers are no longer there.
        self.plugin.create_ticket = True
        # On Unauthorized, redirect to our special headerlogin page.
        self.plugin.redirect_url = '/headerlogin'
        # This is the main user id header.
        self.plugin.userid_header = 'REMOTEUSER'
        transaction.commit()
        self.browser = Browser(self.app)
        self.browser.handleErrors = False

    def _set_referer(self, referer=None):
        # Some zope.testbrowser versions set a Referer, but not all.
        # See https://github.com/zopefoundation/zope.testbrowser/issues/87
        # So we set the referer ourselves.
        if referer is None:
            referer = self.browser.url
        self.browser.addHeader('Referer', referer)

    def test_zope_user_id(self):
        # Users at the zope root always need the headers.
        # The __ac cookie does not get set,
        # because the user is not in the Plone acl_users.
        self.browser.addHeader('REMOTEUSER', SITE_OWNER_NAME)
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url)
        self.assertNotIn('__ac', self.browser.cookies)

        # This user cannot access the overview controlpanel,
        # because the roles are not taken over.
        # This is actually strange, because in /headerlogin above,
        # when I call api.user.get_roles(), I get: ['Manager', 'Authenticated'].
        # So if this next test fails, it would actually be okay.
        with self.assertRaises(Unauthorized):
            self.browser.open(self.portal_url + '/@@overview-controlpanel')

        # We change the userid header in the plugin,
        # so the header in the browser no longer works.
        self.plugin.userid_header = 'NOPE'
        transaction.commit()

        # Now check if we are still authenticated.
        self._set_referer(self.portal_url)
        self.browser.open(self.portal_url + '/headerlogin')
        # We are anonymous, so headerlogin redirects us to standard login.
        self.assertEqual(self.browser.url, self.portal_url + '/login')

    def test_plone_user_name(self):
        # We use a login name here.
        # The __ac cookie does not get set,
        # because we search the user by id, not by login, so no user is found.
        # Note: searching by login, via a different header, could be a new feature.
        self.browser.addHeader('REMOTEUSER', TEST_USER_NAME)
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url)
        self.assertNotIn('__ac', self.browser.cookies)

        # This user cannot access the overview controlpanel.
        with self.assertRaises(Unauthorized):
            self.browser.open(self.portal_url + '/@@overview-controlpanel')

        # We change the userid header in the plugin,
        # so the header in the browser no longer works.
        self.plugin.userid_header = 'NOPE'
        transaction.commit()

        # Now check if we are still authenticated.
        self._set_referer(self.portal_url)
        self.browser.open(self.portal_url + '/headerlogin')
        # We are anonymous, so headerlogin redirects us to standard login.
        self.assertEqual(self.browser.url, self.portal_url + '/login')

    def test_plone_user_id(self):
        # Finally a proper Plone user id.
        self.browser.addHeader('REMOTEUSER', TEST_USER_ID)
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url)
        # Cookie is set.
        self.assertIn('__ac', self.browser.cookies)

        # This user cannot access the overview controlpanel.
        with self.assertRaises(Unauthorized):
            self.browser.open(self.portal_url + '/@@overview-controlpanel')

        # But we can grant roles.
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        transaction.commit()
        self.browser.open(self.portal_url + '/@@overview-controlpanel')

        # We change the userid header in the plugin,
        # so the header in the browser no longer works.
        self.plugin.userid_header = 'NOPE'
        transaction.commit()
        # Now check if we are still authenticated.
        self._set_referer()
        self.browser.open(self.portal_url + '/headerlogin')
        # We are, and we actually get redirected to the referrer, our previous page.
        self.assertEqual(self.browser.url, self.portal_url + '/@@overview-controlpanel')
        self.assertIn('__ac', self.browser.cookies)

    def test_with_roles(self):
        self.plugin.roles_header = 'ROLES'
        transaction.commit()
        self.browser.addHeader('REMOTEUSER', TEST_USER_ID)
        with self.assertRaises(Unauthorized):
            self.browser.open(self.portal_url + '/@@overview-controlpanel')
        self.browser.addHeader('ROLES', 'Manager')
        # Now it works.
        self.browser.open(self.portal_url + '/@@overview-controlpanel')
        self.assertEqual(self.browser.url, self.portal_url + '/@@overview-controlpanel')
        self.assertIn('__ac', self.browser.cookies)

    def test_redirect_from_unauthorized(self):
        # An anonymous user cannot access the overview controlpanel.
        with self.assertRaises(Unauthorized):
            self.browser.open(self.portal_url + '/@@overview-controlpanel')

        # We want to check if the user gets redirected to /headerlogin.
        # But headerlogin redirects us to /login,
        # and I see no way to ask the test browser to not follow redirects.
        # Let's start with letting the browser handle exceptions then.
        self.browser.handleErrors = True
        self.browser.open(self.portal_url + '/@@overview-controlpanel')
        self.assertEqual(self.browser.url, self.portal_url + '/login')

    def test_redirect_url_no_slash(self):
        # The test setUp uses /headerlogin.  Now test without a slash.
        self.plugin.redirect_url = 'headerlogin'
        transaction.commit()
        self.browser.handleErrors = True
        self.browser.open(self.portal_url + '/@@overview-controlpanel')
        self.assertEqual(self.browser.url, self.portal_url + '/login')

    def test_redirect_url_double_slash(self):
        # The test setUp uses /headerlogin.  Now test with double slash.
        # Easiest is to take //nohost/plone/headerlogin without http or https.
        self.plugin.redirect_url = '//' + self.portal_url.split('//')[1] + '/headerlogin'
        transaction.commit()
        self.browser.handleErrors = True
        self.browser.open(self.portal_url + '/@@overview-controlpanel')
        self.assertEqual(self.browser.url, self.portal_url + '/login')

    def test_redirect_url_bytes(self):
        # The redirect url is expected to be a native string both on Py 2 and 3,
        # but I have seen it as bytes on Py 3 in a traceback.
        self.plugin.redirect_url = b'headerlogin'
        transaction.commit()
        self.browser.handleErrors = True
        self.browser.open(self.portal_url + '/@@overview-controlpanel')
        self.assertEqual(self.browser.url, self.portal_url + '/login')

    def test_redirect_came_from_login(self):
        # If we came from a login-related form and are still anonymous,
        # we should not redirect back.  We want to avoid redirect loops.
        with self.assertRaises(Forbidden):
            self.browser.open(
                '{}/headerlogin?came_from={}/require_login'.format(
                    self.portal_url, self.portal_url
                ))

    def test_redirect_referer_login(self):
        # If our referer is a login-related form and we are still anonymous,
        # we should not redirect back.  We want to avoid redirect loops.
        self.browser.open(self.portal_url + '/headerlogin')
        self.assertEqual(self.browser.url, self.portal_url + '/login')
        # Now this login page is the referer for our next request.
        self._set_referer()
        with self.assertRaises(Forbidden):
            self.browser.open(self.portal_url + '/headerlogin')
