# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin  # noqa
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements

import logging


logger = logging.getLogger(__name__)

# This header contains the role.
ROLE_HEADER = 'EA_PROFILE_role'
# Roles that we can handle:
ROLES = [
    'docent',
    'leerling',
]
# Mapping from Plone memberdata property ids to request header ids.
PROPS = {
    'uid': 'EA_PROFILE_uid',
    'voornaam': 'EA_PROFILE_firstname',
    'tussenvoegsel': 'EA_PROFILE_middlename',
    'achternaam': 'EA_PROFILE_lastname',
    'schoolbrin': 'EA_PROFILE_schoolbrin',
    'rol': 'EA_PROFILE_role',
    # We do not need this.
    # 'email': 'EA_PROFILE_email',
}
# Property ids that are only needed temporarily.
# They are used to get the fullname.
TEMP_PROPS = [
    'voornaam',
    'tussenvoegsel',
    'achternaam',
]


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
    except UnicodeDecodeError:
        pass
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


def get_header_role(request):
    """Get role property from the request headers."""
    if request is None:
        return
    role = request.getHeader(ROLE_HEADER)
    if role is None:
        return
    # For one leerling we get role Leerling with capital letter.
    role = role.strip().lower()
    if role not in ROLES:
        logger.error('Unknown role in header: %s', role)
        return
    return role


def get_header_property(request, plone_property):
    """Get a property from the request headers.

    Call this with the name of the Plone portal_memberdata property.
    """
    if request is None:
        return
    header = PROPS.get(plone_property)
    if not header:
        return
    value = request.getHeader(header, '').strip()
    if plone_property == 'rol':
        # For one leerling we get role Leerling with capital letter.
        value = value.lower()
    return value


def get_all_header_properties(request):
    """Get all known properties from the request headers.

    Returns a dictionary.
    """
    result = {}
    if request is None:
        return result
    for plone_prop, header_prop in PROPS.items():
        value = request.getHeader(header_prop, '').strip()
        if plone_prop == 'rol':
            # For one leerling we get role Leerling with capital letter.
            value = value.lower()
        result[plone_prop] = value
    return result


class HeaderPlugin(BasePlugin):
    """PAS Plugin which use information from request headers.

    The headers are trusted: it is the responsibility of a proxy
    to set correct headers and remove any bad headers from hackers.
    """

    meta_type = 'Header Plugin'

    security = ClassSecurityInfo()

    userid_header = ''
    required_headers = ()
    deny_unauthorized = False
    redirect_url = ''
    memberdata_to_header = ()
    _properties = (
        dict(id='userid_header', type='string', mode='w',
             label='Header to use as user id'),
        dict(id='required_headers', type='lines', mode='w',
             label='Required headers.',
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
            response.redirect(self.redirect_url)
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
        creds['request_id'] = self._get_userid(request)
        creds['role'] = get_header_role(request)
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
        request_id = credentials.get('request_id')
        role = credentials.get('role')
        if not (request_id and role):
            return
        return (request_id, request_id)

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

    def _get_userid(self, request):
        """Get userid property from the request headers."""
        if request is None:
            return
        if not self.userid_header:
            return
        return request.getHeader(self.userid_header)

    def _get_all_header_properties(self, request):
        """Get all known properties from the request headers.

        Returns a dictionary.
        """
        result = {}
        if request is None:
            return result
        for line in self.memberdata_to_header:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            if line.count('|') != 1:
                continue
            member_prop, headers = line.split('|')
            member_prop = member_prop.strip()
            if not member_prop:
                continue
            headers = headers.split()
            if not headers:
                continue
            values = [
                request.getHeader(header_prop, '').strip()
                for header_prop in headers]
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
)


def add_header_plugin():
    # Form for manually adding our plugin.
    # But we do this in setuphandlers.py always.
    pass
