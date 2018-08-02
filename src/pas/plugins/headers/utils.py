# -*- coding: utf-8 -*-
from pas.plugins.headers.plugins import HeaderPlugin
from Products.CMFCore.utils import getToolByName


PLUGIN_ID = 'request_headers'


def get_plugin(context):
    pas = getToolByName(context, 'acl_users', None)
    if pas is None:
        # This is too hard to really test, and is really a corner case.
        return  # pragma: no cover
    plugin = getattr(pas, PLUGIN_ID, None)
    if plugin is None:
        return
    if not isinstance(plugin, HeaderPlugin):
        return
    return plugin
