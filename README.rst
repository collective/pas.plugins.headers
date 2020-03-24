.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

===================
pas.plugins.headers
===================

This PAS plugin reads request headers and uses them for authentication.
Think SAML headers that are set by a front web server like Apache or nginx.


Features
--------

On install in Plone, the plugin is added to the ``PluggableAuthService``.
It is registered for several plugin types:

- Challenge plugin
- Extraction plugin
- Authentication plugin
- Properties plugin
- Roles plugin

You can configure them in the ZMI (Zope Management Interface) by editing properties in the plugin.


Installation
------------

Install pas.plugins.headers by adding it to your buildout::

    [buildout]

    ...

    eggs =
        pas.plugins.headers


and then running ``bin/buildout``.
Start Plone and install the plugin in the Add-ons control panel.


Compatibility
-------------

This has been tested to work on Plone 4.3 and 5.1 and 5.2 (Python 2.7 and 3.7).


Plain Zope?
-----------

No, this does not work in plain Zope.
Theoretically it might work if you first install ``Products.PluggableAuthService`` and ``Products.GenericSetup``.
But then you already almost have a ``CMF`` site.


Manual configuration
--------------------

You can configure the plugin by going to the ZMI (Zope Management Interface).
Go to the ``acl_users`` (``PluggableAuthService``) folder in the Plone ZMI.
Click on the ``request_headers`` plugin.
Go to the Properties tab.

These are the properties that you can edit:

``userid_header``:
    Header to use as user id.

``roles_header``:
    Header to use as roles for the current user.
    This can give multiple roles: it is split on white space.

``allowed_roles``:
    Allowed roles.
    Roles that we allow in the ``roles_header``.
    Any other roles that are in the header are ignored.
    Ignored when empty: all roles are taken over, also when the role is not known in Plone.
    The roles from the header and the ``allowed_roles`` property are compared lowercase.
    The reported roles use the case from``allowed_roles``.
    For example, if the header contains ``PUPIL root`` and ``allowed_roles`` contains ``Pupil Teacher``, then the reported roles will be only ``Pupil``.

``required_headers``:
    Required headers.
    Without these, the extraction plugin does not extract headers, so the user is not authenticated.
    These headers may have an empty value in the request, as long as they are all there.

``deny_unauthorized``:
    Deny unauthorized access.
    Default: false.
    When this is true and the user is unauthorized, the Challenge plugin stops and presents an ugly error.
    When false, the Challenge plugin will check the ``redirect_url``.

``redirect_url``:
    URL to redirect to when unauthorized.
    When empty, it has no effect.
    When set, the Challenge plugin redirects unauthorized users to this url.
    Usually you would configure your frontend server to force SAML or CAS login on this url.
    The ``headerlogin`` page defined by this plugin may be a good url.
    We treat the redirect_url as relative to the Plone site root, unless it is a full url.
    If ``deny_unauthorized`` is true, this option is ignored.

``memberdata_to_header``:
    Mapping from memberdata property to request header, one per row.
    Format: ``propname|header``.
    Or: ``propname|header|parser``.
    See the Parsers_ section for information about parsers
    You can also combine several headers:
    ``propname|header_with_firstname header_with_lastname``.

``create_ticket``.
  Create an authentication ticket (``__ac`` cookie) with ``plone.session``.
  Default: false.
  When reading headers, this checks if Plone knows this user.
  If so, we create an authentication ticket.
  Then you could let your frontend server (nginx, Apache) only set the headers for some urls, instead of for all.
  Note that this does not work for root Zope users, and it does not take over properties and roles.
  See also `issue 6 <https://github.com/collective/pas.plugins.headers/issues/6>`_.


Configuration via GenericSetup
------------------------------

The package has a GS (``GenericSetup``) import step with id ``pas.plugins.headers``.
In the GS profile of your add-on, it looks for a file with name ``pas.plugins.headers.json``.
This file must contain a json string.
Full example:

::

    {
        "purge": true,
        "allowed_roles": [
            "Member",
            "Zebra"
        ],
        "create_ticket": true,
        "deny_unauthorized": true,
        "memberdata_to_header": [
            "uid|HEADER_uid|lower",
            "fullname|HEADER_firstname HEADER_lastname"
        ],
        "redirect_url": "https://maurits.vanrees.org",
        "required_headers": [
            "uid",
            "test"
        ],
        "roles_header": "roles",
        "userid_header": "uid"
    }

Some remarks:

- When the contents cannot be parsed as json, or when the result is not a dictionary, a ``ValueError`` is raised.

- ``purge`` is optional.  When it is true, the default settings are restored before handling the rest of the file.

- ``purge`` is only valid for the entire file.
  It does not work in individual lists.
  So you cannot add one required header and keep the current ones.
  You need to specify them all.

- The keys are the properties that you see in the ZMI.

- When an unknown key is used, it is silently ignored.

- In ``memberdata_to_header``, the importer does not check if the parsers are registered.


Parsers
-------

In the ``memberdata_to_header`` property, you can use parsers.
For example::

    age|HEADER_age|int

When getting the properties for the current user, the properties plugin will calculate the ``age`` property.
It reads the ``HEADER_age`` header, which may give a string like ``'42'``.
It then calls the ``int`` parser to turn this into integer ``42``.

Note: the properties plugin is currently the only part where the parsers are used.
So it is not used when getting for example the user id from a header.

If you specify a parser that does not exist, the parser is ignored and you get the unmodified header value.

A few basic parsers are available:

``bool``:
    Returns either True or False.
    When the first character of the lowercase header value is ``y/j/t/1``, the parser return True, else False.

``int``:
    Returns an integer.
    When parsing as integer fails, it returns zero.

``lower``:
    Returns the value in lowercase.

``upper``:
    Returns the value in uppercase.

``split``:
    Splits the value on whitespace, so you get a list.

You can register an own parser::

    def extra_parser(value):
        return value + ' extra'

    from pas.plugins.headers.parsers import register_parser
    register_parser('extra', extra_parser)

Note: you get a warning when you override an existing parser.


Contribute
----------

- Issue tracker: https://github.com/collective/pas.plugins.headers/issues
- Source code: https://github.com/collective/pas.plugins.headers


Support
-------

If you are having issues, please let us know by adding an issue to the tracker: https://github.com/collective/pas.plugins.headers/issues


License
-------

The project is licensed under the GPLv2.
