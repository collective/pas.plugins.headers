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


Plain Zope?
-----------

I would like this to work in plain Zope, but I haven't tested this yet.
You at least need to install ``Products.PluggableAuthService`` and ``Products.GenericSetup`` before you can begin to use this plugin.


Configuration
-------------

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
    If ``deny_unauthorized`` is true, this option is ignored.

``memberdata_to_header``:
    Mapping from memberdata property to request header, one per row.
    Format: ``propname|header``.
    Or: ``propname|header|parser``.
    See the Parsers_ section for information about parsers
    You can also combine several headers:
    ``propname|header_with_firstname header_with_lastname``.


Parsers
-------

In the ``memberdata_to_header`` property, you can use parsers.
For example::

    age|HEADER_age|int

When getting the properties for the current user, the properties plugin will calculate the ``age`` property.
It reads the ``HEADER_age`` header, which may give a string like ``'42'``.
It then calls the ``int`` parser to turn this into integer ``42``.

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
