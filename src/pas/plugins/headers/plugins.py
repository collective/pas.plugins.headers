# -*- coding: utf-8 -*-
from .parsers import parse
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin  # noqa
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements

import logging


logger = logging.getLogger(__name__)
# Marker value for missing headers
_MARKER = object()


def decode_header(value):
    """Decode header to unicode.

    I hope for utf-8 as encoding, but the 'Modify Headers'
    Firefox plugin gives me latin-1.
    The same might be true for the live server.
    """
    if not isinstance(value, basestring):
        return value
    if isinstance(value, unicode):
        return value
    try:
        return value.decode('utf-8')
    except UnicodeDecodeError:
        pass
    try:
        return value.decode('latin-1')
    except UnicodeDecodeError:  # pragma: no cover
        # I don't know how to trigger this in tests.
        return value.decode('utf-8', 'ignore')


def combine_values(values):
    """Combine several values into one.

    Expected use is for getting a fullname from several values.

    For a standard Plone user, member.getProperty('fullname')
    returns an encoded string.  So *no* unicode.
    """
    if not isinstance(values, (list, tuple)):
        return ''
    # filter out empty values.
    values = filter(None, values)
    # Turn values into unicode so we can safely combine them.
    values = [decode_header(value).strip() for value in values]
    # again filter out empty values
    values = filter(None, values)
    full = u' '.join(values)
    # Encode the result.
    return full.encode('utf-8')


class HeaderPlugin(BasePlugin):
    """PAS Plugin which use information from request headers.

    The headers are trusted: it is the responsibility of a proxy
    to set correct headers and remove any bad headers from hackers.
    """

    meta_type = 'Header Plugin'

    security = ClassSecurityInfo()

    userid_header = ''
    roles_header = ''
    allowed_roles = ()
    required_headers = ()
    deny_unauthorized = False
    redirect_url = ''
    memberdata_to_header = ()
    _properties = (
        dict(id='userid_header', type='string', mode='w',
             label='Header to use as user id'),
        dict(id='roles_header', type='string', mode='w',
             label='Header to use as roles'),
        dict(id='allowed_roles', type='lines', mode='w',
             label='Allowed roles'),
        dict(id='required_headers', type='lines', mode='w',
             label='Required headers',
             # Note: description is currently not shown anywhere in the ZMI.
             description='Without these, the plugin does not authenticate.',
             ),
        dict(id='deny_unauthorized', type='boolean', mode='w',
             label='Deny unauthorized access. '
                   'Do not redirect to a login form.'),
        dict(id='redirect_url', type='string', mode='w',
             label='URL to redirect to when unauthorized'),
        dict(id='memberdata_to_header', type='lines', mode='w',
             label='Mapping from memberdata property to request header. '
                   'Format: propname|header1 header2',
             ),
    )

    def challenge(self, request, response):
        """ Assert via the response that credentials will be gathered.

        For IChallengePlugin.

        Takes a REQUEST object and a RESPONSE object.

        Must return True if it fired, False/None otherwise.

        Note: if you are not logged in, and go to the login form,
        everything will still work, and you will not be challenged.
        A challenge is only tried when you are unauthorized.
        """
        if self.deny_unauthorized:
            # We do not give the user a change to login.
            response.write(
                'ERROR: denying any unauthorized access.\n')
            return True
        if self.redirect_url:
            logger.debug('Redirecting to %s', self.redirect_url)
            response.redirect(self.redirect_url, lock=1)
            return True
        # We have no redirect_url, so we do not know how to challenge.
        # Let Plone handle this in the default way, probably showing
        # a login form.
        return

    def extractCredentials(self, request):
        """ request -> {...}

        For IExtractionPlugin.

        o Return a mapping of any derived credentials.

        o Return an empty mapping to indicate that the plugin found no
          appropriate credentials.
        """
        creds = {}
        for header in self.required_headers:
            if request.getHeader(header, _MARKER) is _MARKER:
                return creds
        creds['user_id'] = self._get_userid(request)
        return creds

    def authenticateCredentials(self, credentials):
        """ credentials -> (userid, login)

        For IAuthenticationPlugin.

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a  tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """
        # Check if the credentials are from our own plugin.
        if credentials.get('extractor') != self.getId():
            return
        user_id = credentials.get('user_id')
        if not user_id:
            return
        return (user_id, user_id)

    def getPropertiesForUser(self, user, request=None):
        """ user -> {...}

        For IPropertiesPlugin.

        o User will implement IPropertiedUser.

        o Plugin should return a dictionary or an object providing
          IPropertySheet.

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present

        This is NOT about the properties of the current user,
        but it can be any user.
        If it *is* the current user, we can get the info from the
        request headers.

        """
        if request is None:
            # This seems to only happen for admins.
            return
        user_id = user.getUserId()
        if self._get_userid(request) != user_id:
            return
        return self._get_all_header_properties(request)

    def getRolesForPrincipal(self, principal, request=None):
        """ principal -> ( role_1, ... role_N )

        For IRolesPlugin.

        o Return a sequence of role names which the principal has.

        o May assign roles based on values in the REQUEST object, if present.

        This is NOT about the roles of the current user,
        but it can be any user.
        If it *is* the current user, we can get the info from the
        request headers.
        """
        result = []
        if request is None:
            return result
        if not self.roles_header:
            return result
        user_id = principal.getUserId()
        if self._get_userid(request) != user_id:
            return result
        roles = request.getHeader(self.roles_header)
        if not roles:
            return result
        roles = roles.split()
        if not self.allowed_roles:
            return roles
        # Check roles against the allowed roles.
        # Compare them lowercase.
        # In the result we should only have the spelling from allowed_roles.
        # So prepare a dictionary with keys 'lowercase' and values 'original'.
        allowed_roles = {
            role.lower(): role for role in self.allowed_roles
        }
        for role in roles:
            canonical_role = allowed_roles.get(role.lower())
            if not canonical_role:
                # SAML may give five roles, out of which Plone uses only two.
                logger.debug('Ignoring disallowed role in header: %s', role)
                continue
            result.append(canonical_role)
        return result

    def _get_userid(self, request):
        """Get userid property from the request headers."""
        if request is None:
            return
        if not self.userid_header:
            return
        return request.getHeader(self.userid_header)

    def _parse_memberdata_to_header(self):
        """Parse the memberdata_to_header property."""
        result = []
        for line in self.memberdata_to_header:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            pipes = line.count('|')
            if pipes == 1:
                member_prop, headers = line.split('|')
                parser = None
            elif pipes == 2:
                member_prop, headers, parser = line.split('|')
            else:  # pragma: no cover
                # We are testing for this, but coverage does not see it.
                continue
            member_prop = member_prop.strip()
            if not member_prop:
                continue
            headers = headers.split()
            if not headers:
                continue
            result.append((member_prop, headers, parser))
        return result

    def _get_all_header_properties(self, request):
        """Get all known properties from the request headers.

        Returns a dictionary.
        """
        result = {}
        if request is None:
            return result
        for member_prop, headers, parser in self._parse_memberdata_to_header():
            values = [
                request.getHeader(header_prop, '').strip()
                for header_prop in headers]
            if parser is not None:
                values = [parse(parser, value) for value in values]
            if len(values) == 1:
                result[member_prop] = values[0]
                continue
            result[member_prop] = combine_values(values)

        return result


InitializeClass(HeaderPlugin)

classImplements(
    HeaderPlugin,
    IExtractionPlugin,
    IAuthenticationPlugin,
    IChallengePlugin,
    IPropertiesPlugin,
    IRolesPlugin,
)


def add_header_plugin():
    # Form for manually adding our plugin.
    # But we do this in setuphandlers.py always.
    pass
