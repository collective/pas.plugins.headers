# -*- coding: utf-8 -*-
from pas.plugins.headers.plugins import ROLE_HEADER
from StringIO import StringIO
from zope.publisher.browser import TestRequest
from ZPublisher.HTTPResponse import HTTPResponse

import unittest


class HeaderRequest(TestRequest):

    # TestRequest does not allow writing to attributes, so we do some tricks,
    # trying to avoid sharing a dictionary between all instances.
    headers = None

    def addHeader(self, key, value):
        if self.headers is None:
            self.headers = {}
        self.headers[key] = value

    def getHeader(self, key, default=None):
        if self.headers is None:
            return default
        return self.headers.get(key, default)


class DummyUser(object):

    def __init__(self, userid):
        self.userid = userid

    def getUserId(self):
        return self.userid


class HeaderPluginUnitTests(unittest.TestCase):

    def _makeOne(self):
        # Make a plugin and configure it like we used to have for one client.
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()
        plugin.userid_header = 'EA_PROFILE_uid'
        plugin.required_headers = ('EA_PROFILE_uid', 'EA_PROFILE_role')
        plugin.deny_unauthorized = True
        # plugin.role_header = 'EA_PROFILE_role'
        # plugin.allowed_roles = ['docent', 'leerling']
        plugin.memberdata_to_header = (
            'uid|EA_PROFILE_uid',
            'fullname|EA_PROFILE_firstname '
            'EA_PROFILE_middlename '
            'EA_PROFILE_lastname',
            'schoolbrin|EA_PROFILE_schoolbrin',
            'rol|EA_PROFILE_role|lower',
        )
        return plugin

    def test_decode_header(self):
        from pas.plugins.headers.plugins import decode_header
        self.assertEqual(decode_header(None), None)
        self.assertEqual(decode_header(''), u'')
        self.assertTrue(isinstance(decode_header(''), unicode))
        # u'\xae' is (R)egistered trademark.
        self.assertEqual(decode_header(u'\xae'), u'\xae')  # unicode
        self.assertEqual(decode_header('\xc2\xae'), u'\xae')  # utf-8
        self.assertEqual(decode_header('\xae'), u'\xae')  # latin-1

    def test_combine_values(self):
        from pas.plugins.headers.plugins import combine_values
        self.assertEqual(combine_values(None), u'')
        self.assertEqual(combine_values('My name'), u'')
        self.assertEqual(combine_values({}), u'')
        self.assertEqual(combine_values([]), u'')
        self.assertEqual(combine_values(()), u'')
        self.assertEqual(combine_values(
            ['Maurits']),
            'Maurits')
        # 'Maurits' == u'Maurits' because both contain only ascii.
        # But we *do* want to know if we get unicode or a string back.
        self.assertTrue(isinstance(combine_values(['Maurits']), str))
        self.assertEqual(
            combine_values(['Maurits', 'Rees']),
            'Maurits Rees')
        self.assertEqual(
            combine_values(['Maurits', '', 'Rees']),
            'Maurits Rees')
        self.assertEqual(
            combine_values(['Maurits', 'van', 'Rees']),
            'Maurits van Rees')
        self.assertEqual(
            combine_values(['    Maurits\t\n\r  ', '  ', None, '    Rees \n']),
            'Maurits Rees')
        self.assertEqual(
            combine_values((u'Arthur', u'Dent')),
            'Arthur Dent')
        # In standard Plone we get a string encoded with utf-8.
        self.assertEqual(
            combine_values([u'Arth\xfcr', u'Dent']),
            'Arth\xc3\xbcr Dent')
        self.assertTrue(isinstance(combine_values([u'Arth\xfcr']), str))
        # We can combine more than three.
        self.assertEqual(
            combine_values(['', 'Hello,', 'Maurits', '   ' 'van', 'Rees']),
            'Hello, Maurits van Rees')
        # And they can be unicode / encoded string / ascii string.
        self.assertEqual(
            combine_values(['Dent', u'Arth\xfcr', u'Dent', 'Arth\xc3\xbcr']),
            'Dent Arth\xc3\xbcr Dent Arth\xc3\xbcr')

    def test_get_userid(self):
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()
        auth_header = 'SAML_id'
        request = HeaderRequest()
        self.assertEqual(plugin._get_userid(request), None)
        request.addHeader(auth_header, 'foo')
        self.assertEqual(plugin._get_userid(request), None)
        # Specify the userid_header that the plugin must look for.
        plugin.userid_header = auth_header
        self.assertEqual(plugin._get_userid(request), 'foo')
        request = HeaderRequest()
        self.assertEqual(plugin._get_userid(request), None)

    def test_get_header_role(self):
        from pas.plugins.headers.plugins import get_header_role
        request = HeaderRequest()
        self.assertEqual(get_header_role(request), None)
        request.addHeader(ROLE_HEADER, 'foo')
        self.assertEqual(get_header_role(request), None)
        # Only two values are accepted.
        request.addHeader(ROLE_HEADER, 'docent')
        self.assertEqual(get_header_role(request), 'docent')
        request.addHeader(ROLE_HEADER, 'leerling')
        self.assertEqual(get_header_role(request), 'leerling')
        # Well, we may accept capitalised values.
        request.addHeader(ROLE_HEADER, 'Leerling')
        self.assertEqual(get_header_role(request), 'leerling')
        request.addHeader(ROLE_HEADER, 'LEERLING    ')
        self.assertEqual(get_header_role(request), 'leerling')

    def test_parse_memberdata_to_header(self):
        plugin = self._makeOne()
        self.assertEqual(
            plugin._parse_memberdata_to_header(),
            [
                ('uid', ['EA_PROFILE_uid'], None),
                ('fullname',
                 [
                     'EA_PROFILE_firstname',
                     'EA_PROFILE_middlename',
                     'EA_PROFILE_lastname',
                 ],
                 None
                 ),
                ('schoolbrin', ['EA_PROFILE_schoolbrin'], None),
                ('rol', ['EA_PROFILE_role'], 'lower'),
            ]
        )

    def test_get_all_header_properties(self):
        plugin = self._makeOne()
        auth_header = plugin.userid_header
        request = HeaderRequest()
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {'fullname': '',
             'rol': '',
             'schoolbrin': '',
             'uid': '',
             })
        request.addHeader('EA_PROFILE_foo', 'bar')
        request.addHeader('EA_PROFILE_firstname', 'Maurits')
        request.addHeader('EA_PROFILE_middlename', 'van')
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {'fullname': 'Maurits van',
             'rol': '',
             'schoolbrin': '',
             'uid': '',
             })
        request.addHeader('EA_PROFILE_lastname', 'Rees')
        request.addHeader('EA_PROFILE_schoolbrin', 'AA44ZT')
        request.addHeader(auth_header, 'my uid')
        request.addHeader(ROLE_HEADER, 'docent')
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {'fullname': 'Maurits van Rees',
             'rol': 'docent',
             'schoolbrin': 'AA44ZT',
             'uid': 'my uid',
             })

    def test_no_challenge(self):
        # By default we do not challenge, because we do not know how.
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()

        # Prepare the request.
        request = HeaderRequest()
        out = StringIO()
        response = HTTPResponse(stdout=out)

        # When the plugin does not make a challenge, it must not return a
        # value.
        self.assertFalse(plugin.challenge(request, response))

        # Check the response.
        out.seek(0)
        self.assertNotIn(
            'Fout: Geen authenticatie headers gevonden.',
            out.read())

    def test_challenge_deny(self):
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()
        plugin.deny_unauthorized = True

        # Prepare the request.
        request = HeaderRequest()
        out = StringIO()
        response = HTTPResponse(stdout=out)

        # When the plugin makes a challenge, it must return a True value.
        self.assertTrue(plugin.challenge(request, response))

        # Check the response.
        out.seek(0)
        self.assertIn(
            'ERROR: denying any unauthorized access.',
            out.read())

    def test_challenge_redirect(self):
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()
        url = 'https://example.org/saml-login'
        plugin.redirect_url = url

        # Prepare the request.
        request = HeaderRequest()
        out = StringIO()
        response = HTTPResponse(stdout=out)

        # When the plugin makes a challenge, it must return a True value.
        self.assertTrue(plugin.challenge(request, response))

        # Check the response.
        out.seek(0)
        self.assertEqual(out.read(), '')
        self.assertEqual(response.headers['location'], url)

    def test_extractCredentials(self):
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()
        auth_header = 'SAML_id'
        plugin.userid_header = auth_header
        request = HeaderRequest()
        self.assertEqual(plugin.extractCredentials(request),
                         {'role': None, 'request_id': None})
        request.addHeader(auth_header, 'my uid')
        self.assertEqual(plugin.extractCredentials(request),
                         {'role': None, 'request_id': 'my uid'})
        request.addHeader(ROLE_HEADER, 'pupil')
        self.assertEqual(plugin.extractCredentials(request),
                         {'role': None, 'request_id': 'my uid'})
        request.addHeader(ROLE_HEADER, 'leerling')
        self.assertEqual(plugin.extractCredentials(request),
                         {'role': 'leerling', 'request_id': 'my uid'})
        request.addHeader(ROLE_HEADER, 'Leerling   ')
        self.assertEqual(plugin.extractCredentials(request),
                         {'role': 'leerling', 'request_id': 'my uid'})

        # Now test with required_headers
        plugin.required_headers = ('HEADER1', 'HEADER2')
        self.assertEqual(plugin.extractCredentials(request), {})
        request.addHeader('HEADER1', '')
        self.assertEqual(plugin.extractCredentials(request), {})
        request.addHeader('HEADER2', '')
        self.assertEqual(plugin.extractCredentials(request),
                         {'role': 'leerling', 'request_id': 'my uid'})

    def test_authenticateCredentials(self):
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin()
        plugin.id = 'my_plugin'
        self.assertIsNone(plugin.authenticateCredentials({}))
        self.assertIsNone(plugin.authenticateCredentials({
            'role': 'leerling', 'request_id': '123'
        }))
        self.assertEqual(plugin.authenticateCredentials({
            'role': 'leerling', 'request_id': '123', 'extractor': 'my_plugin'
        }), ('123', '123'))
        self.assertIsNone(plugin.authenticateCredentials({
            'request_id': '123', 'extractor': 'my_plugin'
        }))
        self.assertIsNone(plugin.authenticateCredentials({
            'role': 'leerling', 'extractor': 'my_plugin'
        }))

    def test_getPropertiesForUser(self):
        # from pas.plugins.headers.plugins import HeaderPlugin
        # plugin = HeaderPlugin()
        plugin = self._makeOne()
        auth_header = plugin.userid_header
        user = DummyUser('maurits')
        self.assertIsNone(plugin.getPropertiesForUser(user))
        request = HeaderRequest()
        self.assertIsNone(plugin.getPropertiesForUser(user, request))
        request.addHeader(auth_header, 'pipo')
        # user id and auth header must be the same
        self.assertIsNone(plugin.getPropertiesForUser(user, request))
        request.addHeader(auth_header, 'maurits')
        self.assertEqual(
            plugin.getPropertiesForUser(user, request),
            {'fullname': '',
             'rol': '',
             'schoolbrin': '',
             'uid': 'maurits'})
        request.addHeader('EA_PROFILE_firstname', 'Maurits')
        request.addHeader('EA_PROFILE_middlename', 'van')
        request.addHeader('EA_PROFILE_lastname', 'Rees')
        request.addHeader('EA_PROFILE_schoolbrin', 'AA44ZT')
        request.addHeader(ROLE_HEADER, 'docent')
        self.assertEqual(
            plugin.getPropertiesForUser(user, request),
            {'fullname': 'Maurits van Rees',
             'rol': 'docent',
             'schoolbrin': 'AA44ZT',
             'uid': 'maurits'})
        request.addHeader(ROLE_HEADER, '  LEERling  \t ')
        self.assertEqual(
            plugin.getPropertiesForUser(user, request),
            {'fullname': 'Maurits van Rees',
             'rol': 'leerling',
             'schoolbrin': 'AA44ZT',
             'uid': 'maurits'})
        arthur = DummyUser('arthur')
        self.assertIsNone(plugin.getPropertiesForUser(arthur, request))
