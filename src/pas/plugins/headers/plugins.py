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

# This is the main authentication header.
AUTH_HEADER = 'EA_PROFILE_uid'
# This header contains the role.
ROLE_HEADER = 'EA_PROFILE_role'
# Roles that we can handle:
ROLES = [
    'docent',
    'leerling',
]
# Mapping from Plone memberdata property ids to request header ids.
PROPS = {
    'uid': AUTH_HEADER,
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


def get_fullname(props):
    """Get fullname from properties.

    For a standard Plone user, member.getProperty('fullname')
    returns an encoded string.  So *no* unicode.
    """
    if not isinstance(props, dict):
        return ''
    firstname = decode_header(props.get('voornaam', ''))
    prefix = decode_header(props.get('tussenvoegsel', ''))
    surname = decode_header(props.get('achternaam', ''))
    fullname = u'{0} {1} {2}'.format(firstname, prefix, surname)
    # The next line removes double spaces when there is no prefix.
    fullname = u' '.join(fullname.split())
    fullname = fullname.encode('utf-8')
    return fullname


def get_header_uid(request):
    """Get uid property from the request headers."""
    if request is None:
        return
    return request.getHeader(AUTH_HEADER)


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

    def challenge(self, request, response):
        """ Assert via the response that credentials will be gathered.

        For IChallengePlugin.

        Takes a REQUEST object and a RESPONSE object.

        Returns True if it fired, False otherwise.

        In our case, we can either give an error,
        or redirect to some page elsewhere.
        But when there is no auth header, the proxy will already
        stop the user.  So giving an error is fine.

        We could check the domain: do not challenge when you are on cms
        or 127.0.0.1.  But we would need to watch out for virtual host
        rewriting then.  Anyway, if you are not logged in, and go to
        the login form, everything will still work, and you will not
        be challenged.
        """
        if get_header_uid(request) and get_header_role(request):
            return
        logger.error('Error: No authentication request headers found.')
        response.write(
            'Fout: Geen correcte authenticatie headers gevonden.\n')
        return True

    def extractCredentials(self, request):
        """ request -> {...}

        For IExtractionPlugin.

        o Return a mapping of any derived credentials.

        o Return an empty mapping to indicate that the plugin found no
          appropriate credentials.
        """
        creds = {}
        creds['request_id'] = get_header_uid(request)
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
        if get_header_uid(request) != user_id:
            return
        props = get_all_header_properties(request)
        # Instead of first/middle/last name, we only need fullname.
        props['fullname'] = get_fullname(props)
        for prop in TEMP_PROPS:
            props.pop(prop, None)
        return props


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
