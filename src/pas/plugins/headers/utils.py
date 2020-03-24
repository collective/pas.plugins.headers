# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName

import six


PLUGIN_ID = 'request_headers'


def get_plugin(context):
    pas = getToolByName(context, 'acl_users', None)
    if pas is None:
        # This is too hard to really test, and is really a corner case.
        return  # pragma: no cover
    plugin = getattr(pas, PLUGIN_ID, None)
    if plugin is None:
        return

    # Import here to avoid a circular import
    from pas.plugins.headers.plugins import HeaderPlugin

    if not isinstance(plugin, HeaderPlugin):
        return
    return plugin


def safe_make_string(value):
    """Make bytes/text value a string.

    If value is a list/tuple, do this for each item.  Return a list.

    If a value is an integer or some other non-bytes/string/text type,
    let it remain the same.
    """
    if isinstance(value, (list, tuple, set)):
        return [safe_make_string(v) for v in value]
    try:
        return six.ensure_str(value)
    except TypeError:
        return value
