# -*- coding: utf-8 -*-
"""Init and utils."""
from AccessControl.Permissions import manage_users as ManageUsers
from Products.PluggableAuthService.PluggableAuthService import registerMultiPlugin  # noqa
from zope.i18nmessageid import MessageFactory


_ = MessageFactory('pas.plugins.headers')


def initialize(context):  # pragma: no cover
    """Initializer called when used as a Zope 2 product."""
    from pas.plugins.headers import plugins

    registerMultiPlugin(plugins.HeaderPlugin.meta_type)

    context.registerClass(
        plugins.HeaderPlugin,
        permission=ManageUsers,
        constructors=(
            plugins.add_header_plugin, ),
        # icon='www/PluggableAuthService.png',
    )
