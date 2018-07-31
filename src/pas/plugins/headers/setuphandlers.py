# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer

import logging


logger = logging.getLogger(__name__)


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'pas.plugins.headers:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # Setup our request header plugin.
    pas = getToolByName(context, 'acl_users')
    ID = 'request_headers'

    # Create plugin if it does not exist.
    if ID not in pas.objectIds():
        from pas.plugins.headers.plugins import HeaderPlugin
        plugin = HeaderPlugin(
            title='Request Headers',
        )
        plugin.id = ID
        pas._setObject(ID, plugin)
        logger.info('Created %s in acl_users.', ID)
    plugin = getattr(pas, ID)

    # Activate all supported interfaces for this plugin.
    activate = []
    plugins = pas.plugins
    for info in plugins.listPluginTypeInfo():
        interface = info['interface']
        interface_name = info['id']
        if plugin.testImplements(interface):
            activate.append(interface_name)
            logger.info(
                'Activating interface %s for plugin %s',
                interface_name, info['title'])

    plugin.manage_activateInterfaces(activate)
    logger.info('Plugins activated.')

    # Order some plugins to make sure our plugin is at the top.
    # This is not needed for all plugin interfaces.
    for info in plugins.listPluginTypeInfo():
        interface_name = info['id']
        if interface_name in ['IChallengePlugin', 'IPropertiesPlugin']:
            iface = plugins._getInterfaceFromName(interface_name)
            for obj in plugins.listPlugins(iface):
                plugins.movePluginsUp(iface, [ID])
            logger.info('Moved %s to top of %s.', ID, interface_name)


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
