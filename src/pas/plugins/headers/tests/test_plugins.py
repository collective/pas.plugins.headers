from io import BytesIO
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

    def removeHeader(self, key):
        if key in self.headers:
            del self.headers[key]

    def getHeader(self, key, default=None):
        if self.headers is None:
            return default
        return self.headers.get(key, default)


class DummyUser:
    def __init__(self, userid):
        self.userid = userid

    def getUserId(self):
        return self.userid


class HeaderPluginUnitTests(unittest.TestCase):
    def _makeOne(self):
        # Make a plugin and configure it like we used to have for one client.
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        plugin.userid_header = "EA_PROFILE_uid"
        plugin.required_headers = ("EA_PROFILE_uid", "EA_PROFILE_role")
        plugin.deny_unauthorized = True
        plugin.create_ticket = True
        plugin.roles_header = "EA_PROFILE_role"
        plugin.allowed_roles = ("docent", "leerling")
        plugin.memberdata_to_header = (
            "uid|EA_PROFILE_uid",
            "fullname|EA_PROFILE_firstname "
            "EA_PROFILE_middlename "
            "EA_PROFILE_lastname",
            "schoolbrin|EA_PROFILE_schoolbrin",
            "rol|EA_PROFILE_role|lower",
        )
        return plugin

    def test_decode_header(self):
        from pas.plugins.headers.plugins import decode_header

        self.assertEqual(decode_header(None), None)
        self.assertEqual(decode_header(""), "")
        self.assertEqual(decode_header(b""), "")
        self.assertTrue(isinstance(decode_header(""), str))
        # '\xae' is (R) registered trademark.
        self.assertEqual(decode_header("\xae"), "\xae")  # unicode
        self.assertEqual(decode_header(b"\xc2\xae"), "\xae")  # utf-8
        self.assertEqual(decode_header(b"\xae"), "\xae")  # latin-1

    def test_combine_values(self):
        from pas.plugins.headers.plugins import combine_values

        self.assertEqual(combine_values(None), "")
        self.assertEqual(combine_values("My name"), "")
        self.assertEqual(combine_values({}), "")
        self.assertEqual(combine_values([]), "")
        self.assertEqual(combine_values(()), "")
        self.assertEqual(combine_values([b"Maurits"]), "Maurits")
        self.assertEqual(combine_values(["Maurits"]), "Maurits")
        self.assertTrue(isinstance(combine_values(["Maurits"]), str))
        self.assertEqual(combine_values(["Maurits", "Rees"]), "Maurits Rees")
        self.assertEqual(combine_values(["Maurits", "", "Rees"]), "Maurits Rees")
        self.assertEqual(combine_values(["Maurits", "van", "Rees"]), "Maurits van Rees")
        self.assertEqual(
            combine_values(["    Maurits\t\n\r  ", "  ", None, "    Rees \n"]),
            "Maurits Rees",
        )
        self.assertEqual(combine_values(("Arthur", "Dent")), "Arthur Dent")

        arthur = "Arth\xfcr"
        self.assertEqual(combine_values([b"Arth\xc3\xbcr", b"Dent"]), arthur + " Dent")
        self.assertTrue(isinstance(combine_values([b"Arth\xc3\xbcr"]), str))
        self.assertEqual(combine_values(["Arth\xfcr", "Dent"]), arthur + " Dent")
        self.assertTrue(isinstance(combine_values(["Arth\xfcr"]), str))

        # We can combine more than three.
        self.assertEqual(
            combine_values(["", "Hello,", "Maurits", "   " "van", "Rees"]),
            "Hello, Maurits van Rees",
        )
        # And they can be unicode / encoded string / ascii string.
        self.assertEqual(
            combine_values([b"Dent", "Arth\xfcr", "Dent", b"Arth\xc3\xbcr", arthur]),
            "Dent {0} Dent {0} {0}".format(arthur),
        )

    def test_get_userid(self):
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        auth_header = "SAML_id"
        self.assertEqual(plugin._get_userid(None), None)
        request = HeaderRequest()
        self.assertEqual(plugin._get_userid(request), None)
        request.addHeader(auth_header, "foo")
        self.assertEqual(plugin._get_userid(request), None)
        # Specify the userid_header that the plugin must look for.
        plugin.userid_header = auth_header
        self.assertEqual(plugin._get_userid(request), "foo")
        request = HeaderRequest()
        self.assertEqual(plugin._get_userid(request), None)

    def test_getRolesForPrincipal(self):
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        auth_header = "SAML_ID"
        roles_header = "SAML_roles"
        plugin.userid_header = auth_header
        plugin.roles_header = roles_header
        user = DummyUser("maurits")
        self.assertEqual(plugin.getRolesForPrincipal(user, None), [])
        request = HeaderRequest()
        self.assertEqual(plugin.getRolesForPrincipal(user, request), [])
        # We need a roles header.
        request.addHeader(roles_header, "student")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), [])
        # We need an auth header.
        request.addHeader(auth_header, "pipo")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), [])
        # The auth header needs to be for the current user.
        request.addHeader(auth_header, "maurits")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), ["student"])
        # Try an empty roles header.
        request.addHeader(roles_header, "")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), [])
        # Try missing roles header.
        request.removeHeader(roles_header)
        self.assertEqual(plugin.getRolesForPrincipal(user, request), [])
        # White space is stripped, case is kept by default.
        request.addHeader(roles_header, "  STUDENT    ")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), ["STUDENT"])
        # Multiple roles can be set.
        request.addHeader(roles_header, "  one two three   ")
        self.assertEqual(
            plugin.getRolesForPrincipal(user, request), ["one", "three", "two"]
        )
        # We can restrict the roles that we take over.
        plugin.allowed_roles = ("one", "three")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), ["one", "three"])
        # Case is kept from these canonical roles.
        request.addHeader(roles_header, "ONE Two Three")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), ["one", "three"])
        plugin.allowed_roles = ("One", "THRee")
        self.assertEqual(plugin.getRolesForPrincipal(user, request), ["One", "THRee"])
        # We may have default roles, when the automatic Authenticated role
        # is not enough.
        plugin.default_roles = ("Member",)
        self.assertEqual(
            plugin.getRolesForPrincipal(user, request), ["Member", "One", "THRee"]
        )
        plugin.default_roles = ("Member", "Raccoon")
        self.assertEqual(
            plugin.getRolesForPrincipal(user, request),
            ["Member", "One", "Raccoon", "THRee"],
        )
        # If we unset the roles_header, no roles are found, except the default roles.
        plugin.roles_header = ""
        self.assertEqual(
            plugin.getRolesForPrincipal(user, request), ["Member", "Raccoon"]
        )
        plugin.default_roles = ()
        self.assertEqual(plugin.getRolesForPrincipal(user, request), [])

    def test_parse_memberdata_to_header(self):
        plugin = self._makeOne()
        self.assertEqual(
            plugin._parse_memberdata_to_header(),
            [
                ("uid", ["EA_PROFILE_uid"], None),
                (
                    "fullname",
                    [
                        "EA_PROFILE_firstname",
                        "EA_PROFILE_middlename",
                        "EA_PROFILE_lastname",
                    ],
                    None,
                ),
                ("schoolbrin", ["EA_PROFILE_schoolbrin"], None),
                ("rol", ["EA_PROFILE_role"], "lower"),
            ],
        )

        # Test some corner cases.
        plugin.memberdata_to_header = ()
        self.assertEqual(plugin._parse_memberdata_to_header(), [])
        plugin.memberdata_to_header = ("",)
        self.assertEqual(plugin._parse_memberdata_to_header(), [])
        plugin.memberdata_to_header = ("  hi     |     there     ",)
        self.assertEqual(
            plugin._parse_memberdata_to_header(), [("hi", ["there"], None)]
        )
        plugin.memberdata_to_header = (
            "# ignore|me",
            "hi|there",
        )
        self.assertEqual(
            plugin._parse_memberdata_to_header(), [("hi", ["there"], None)]
        )
        plugin.memberdata_to_header = (
            "too|many|pipes|for|me",
            "hi|there",
        )
        self.assertEqual(
            plugin._parse_memberdata_to_header(), [("hi", ["there"], None)]
        )
        plugin.memberdata_to_header = (
            "   |missing_memberdata",
            "hi|there",
        )
        self.assertEqual(
            plugin._parse_memberdata_to_header(), [("hi", ["there"], None)]
        )
        plugin.memberdata_to_header = (
            "missing_headers|   ",
            "hi|there",
        )
        self.assertEqual(
            plugin._parse_memberdata_to_header(), [("hi", ["there"], None)]
        )

    def test_get_all_header_properties(self):
        plugin = self._makeOne()
        auth_header = plugin.userid_header
        roles_header = plugin.roles_header
        self.assertEqual(plugin._get_all_header_properties(None), {})
        request = HeaderRequest()
        plugin._get_all_header_properties(request)
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {
                "fullname": "",
                "rol": "",
                "schoolbrin": "",
                "uid": "",
            },
        )
        request.addHeader("EA_PROFILE_foo", "bar")
        request.addHeader("EA_PROFILE_firstname", "Maurits")
        request.addHeader("EA_PROFILE_middlename", "van")
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {
                "fullname": "Maurits van",
                "rol": "",
                "schoolbrin": "",
                "uid": "",
            },
        )
        request.addHeader("EA_PROFILE_lastname", "Rees")
        request.addHeader("EA_PROFILE_schoolbrin", "AA44ZT")
        request.addHeader(auth_header, "my uid")
        request.addHeader(roles_header, "docent")
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {
                "fullname": "Maurits van Rees",
                "rol": "docent",
                "schoolbrin": "AA44ZT",
                "uid": "my uid",
            },
        )
        request.addHeader("EA_PROFILE_lastname", "Rees")
        request.addHeader("EA_PROFILE_schoolbrin", "AA44ZT")
        request.addHeader(auth_header, "my uid")
        request.addHeader(roles_header, "docent")
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {
                "fullname": "Maurits van Rees",
                "rol": "docent",
                "schoolbrin": "AA44ZT",
                "uid": "my uid",
            },
        )

        # Whitespace within a header is kept.
        # If you want a list in your data, you can use the 'split' parser.
        request.addHeader("test", "one two")
        plugin.memberdata_to_header = (
            "a|test",
            "b|test|split",
        )
        self.assertEqual(
            plugin._get_all_header_properties(request),
            {
                "a": "one two",
                "b": ["one", "two"],
            },
        )

    def test_no_challenge(self):
        # By default we do not challenge, because we do not know how.
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()

        # Prepare the request.
        request = HeaderRequest()
        out = BytesIO()
        response = HTTPResponse(stdout=out)

        # When the plugin does not make a challenge, it must not return a
        # value.
        self.assertFalse(plugin.challenge(request, response))

        # Check the response.
        out.seek(0)
        self.assertFalse(out.read())

    def test_challenge_deny(self):
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        plugin.deny_unauthorized = True

        # Prepare the request.
        request = HeaderRequest()
        out = BytesIO()
        response = HTTPResponse(stdout=out)

        # When the plugin makes a challenge, it must return a True value.
        self.assertTrue(plugin.challenge(request, response))

        # Check the response.
        out.seek(0)
        # Yes, this must be bytes, not 'str' on Python 3.
        self.assertIn(b"ERROR: denying any unauthorized access.", out.read())

    def test_challenge_redirect(self):
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        url = "https://example.org/saml-login"
        plugin.redirect_url = url

        # Prepare the request.
        request = HeaderRequest()
        out = BytesIO()
        response = HTTPResponse(stdout=out)

        # When the plugin makes a challenge, it must return a True value.
        self.assertTrue(plugin.challenge(request, response))

        # Check the response.
        out.seek(0)
        self.assertEqual(out.read(), b"")
        self.assertEqual(response.getStatus(), 302)  # Check for Redirect
        self.assertEqual(response.headers["location"], f"{url}?came_from={request.URL}")

    def test_challenge_break_redirect_cycle(self):
        # Prepare the plugin.
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        url = "https://example.org/saml-login"
        plugin.redirect_url = url

        # Prepare the request.
        request = HeaderRequest()
        auth_header = "SAML_id"
        plugin.userid_header = auth_header
        request.addHeader(auth_header, "my uid")
        out = BytesIO()
        response = HTTPResponse(stdout=out)

        # When the plugin does not make a challenge, it must returns None
        self.assertIsNone(plugin.challenge(request, response))

        # Check the response -  it must not contain a redirection ("location")
        out.seek(0)
        self.assertEqual(out.read(), b"")
        self.assertEqual(response.getStatus(), 200)
        self.assertIsNone(response.headers.get("location"))

    def test_extractCredentials(self):
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        auth_header = "SAML_id"
        plugin.userid_header = auth_header
        request = HeaderRequest()
        self.assertEqual(plugin.extractCredentials(request), {"user_id": None})
        request.addHeader(auth_header, "my uid")
        self.assertEqual(plugin.extractCredentials(request), {"user_id": "my uid"})

        # Now test with required_headers
        plugin.required_headers = ("HEADER1", "HEADER2")
        self.assertEqual(plugin.extractCredentials(request), {})
        request.addHeader("HEADER1", "")
        self.assertEqual(plugin.extractCredentials(request), {})
        request.addHeader("HEADER2", "")
        self.assertEqual(plugin.extractCredentials(request), {"user_id": "my uid"})

    def test_authenticateCredentials(self):
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()
        plugin.id = "my_plugin"
        self.assertIsNone(plugin.authenticateCredentials({}))
        self.assertIsNone(plugin.authenticateCredentials({"user_id": "123"}))
        self.assertIsNone(plugin.authenticateCredentials({"extractor": "my_plugin"}))
        self.assertIsNone(
            plugin.authenticateCredentials({"user_id": "", "extractor": "my_plugin"})
        )
        self.assertEqual(
            plugin.authenticateCredentials(
                {"user_id": "123", "extractor": "my_plugin"}
            ),
            ("123", "123"),
        )

    def test_getPropertiesForUser(self):
        # from pas.plugins.headers.plugins import HeaderPlugin
        # plugin = HeaderPlugin()
        plugin = self._makeOne()
        auth_header = plugin.userid_header
        roles_header = plugin.roles_header
        user = DummyUser("maurits")
        self.assertIsNone(plugin.getPropertiesForUser(user))
        request = HeaderRequest()
        self.assertIsNone(plugin.getPropertiesForUser(user, request))
        request.addHeader(auth_header, "pipo")
        # user id and auth header must be the same
        self.assertIsNone(plugin.getPropertiesForUser(user, request))
        request.addHeader(auth_header, "maurits")
        self.assertEqual(
            plugin.getPropertiesForUser(user, request),
            {"fullname": "", "rol": "", "schoolbrin": "", "uid": "maurits"},
        )
        request.addHeader("EA_PROFILE_firstname", "Maurits")
        request.addHeader("EA_PROFILE_middlename", "van")
        request.addHeader("EA_PROFILE_lastname", "Rees")
        request.addHeader("EA_PROFILE_schoolbrin", "AA44ZT")
        request.addHeader(roles_header, "docent")
        self.assertEqual(
            plugin.getPropertiesForUser(user, request),
            {
                "fullname": "Maurits van Rees",
                "rol": "docent",
                "schoolbrin": "AA44ZT",
                "uid": "maurits",
            },
        )
        request.addHeader(roles_header, "  LEERling  \t ")
        self.assertEqual(
            plugin.getPropertiesForUser(user, request),
            {
                "fullname": "Maurits van Rees",
                "rol": "leerling",
                "schoolbrin": "AA44ZT",
                "uid": "maurits",
            },
        )
        arthur = DummyUser("arthur")
        self.assertIsNone(plugin.getPropertiesForUser(arthur, request))

    def test_add_header_plugin(self):
        # We could create a function or form for adding the plugin manually,
        # but we prefer to do this via GenericSetup.
        # Maybe it is easy.
        # Anyway, we *do* need to register such a function.
        # So let's at least call it and see that nothing breaks.
        from pas.plugins.headers.plugins import add_header_plugin

        add_header_plugin()

    def test_resetCredentials(self):
        from pas.plugins.headers.plugins import HeaderPlugin

        plugin = HeaderPlugin()

        # On logout, the plugin may want to remove some cookies.
        # Calling it on a non-authenticated request without cookies
        # should not give an error.
        request = HeaderRequest()
        plugin.resetCredentials(request, request.response)

        # Configure the plugin and add some cookies to the request.
        plugin.cookies_removed_on_logout = ("away",)
        request = HeaderRequest(environ={"HTTP_COOKIE": "keep=1, away=1"})
        self.assertEqual(sorted(request.cookies.keys()), ["away", "keep"])
        plugin.resetCredentials(request, request.response)
        # The 'away' cookies is removed by the response:
        self.assertTrue(request.response.getCookie("away")["expires"])
        self.assertEqual(request.response.getCookie("away")["max_age"], 0)
        self.assertEqual(request.response.getCookie("away")["value"], "deleted")
        # The response does nothing with the 'keep' cookie:
        self.assertFalse(request.response.getCookie("keep"))

        # You can use a wildcard at the end.
        plugin.cookies_removed_on_logout = ("a*",)
        request = HeaderRequest(environ={"HTTP_COOKIE": "a=1, always=1, ba=1"})
        self.assertEqual(sorted(request.cookies.keys()), ["a", "always", "ba"])
        plugin.resetCredentials(request, request.response)
        # All cookies starting with 'a' are removed by the response:
        self.assertTrue(request.response.getCookie("a")["expires"])
        self.assertEqual(request.response.getCookie("a")["max_age"], 0)
        self.assertEqual(request.response.getCookie("a")["value"], "deleted")
        self.assertTrue(request.response.getCookie("always")["expires"])
        self.assertEqual(request.response.getCookie("always")["max_age"], 0)
        self.assertEqual(request.response.getCookie("always")["value"], "deleted")
        # The response does nothing with the other cookie:
        self.assertFalse(request.response.getCookie("ba"))
